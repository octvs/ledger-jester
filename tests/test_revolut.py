# Written by AI.

from pathlib import Path

import pandas as pd
import pytest

from parsers import get_parser
from parsers.banks.revolut import RevolutParser

FIXTURE = Path(__file__).parent / "fixtures" / "revolut_sample.csv"

EXPECTED_COLUMNS = [
    "Type",
    "Product",
    "Started Date",
    "Completed Date",
    "Description",
    "Amount",
    "Fee",
    "Currency",
    "State",
    "Balance",
]


def test_registry_returns_revolut_parser():
    parser = get_parser("revolut")
    assert isinstance(parser, RevolutParser)


def test_read_file_dt_matches_completed_date():
    """dt must be a faithful parse of Completed Date, not just present."""
    parser = RevolutParser()
    df = parser.read_file(FIXTURE)

    expected = pd.to_datetime(df["Completed Date"], format="%Y-%m-%d %H:%M:%S")
    pd.testing.assert_series_equal(df["dt"], expected, check_names=False)


def test_read_file_numeric_columns_are_numeric():
    """Guards against decimal/thousands misparsing (as happened with CeptTEB)."""
    parser = RevolutParser()
    df = parser.read_file(FIXTURE)

    for col in ("Amount", "Fee", "Balance"):
        assert pd.api.types.is_float_dtype(df[col]), (
            f"{col} expected float dtype, got {df[col].dtype}"
        )


def test_read_file_preserves_original_schema():
    """dt is an internal-only column; original export schema must be untouched.

    This is what allows downstream sync scripts to auto-detect export
    type by column signature.
    """
    parser = RevolutParser()
    df = parser.read_file(FIXTURE)

    assert [c for c in df.columns if c != "dt"] == EXPECTED_COLUMNS


def test_read_file_wrong_extension_raises(tmp_path):
    bad_file = tmp_path / "export.txt"
    bad_file.write_text("not a csv")

    parser = RevolutParser()
    with pytest.raises(ValueError, match="Unsupported file extension"):
        parser.read_file(bad_file)


def test_read_file_missing_required_column_raises(tmp_path):
    bad_csv = tmp_path / "broken.csv"
    bad_csv.write_text("Type,Product,Amount\nTransfer,Current,10.00\n")

    parser = RevolutParser()
    with pytest.raises(KeyError, match="Completed Date"):
        parser.read_file(bad_csv)


def test_read_file_empty_file_raises(tmp_path):
    empty_csv = tmp_path / "empty.csv"
    empty_csv.write_text("")

    parser = RevolutParser()
    with pytest.raises(pd.errors.EmptyDataError):
        parser.read_file(empty_csv)


def test_preprocess_groups_sorts_by_dt_and_product():
    df = pd.DataFrame(
        {
            "dt": pd.to_datetime(["2024-01-02", "2024-01-01", "2024-01-01"]),
            "Product": ["Current", "Deposit", "Current"],
            "Amount": [1, 2, 3],
        }
    )
    parser = RevolutParser()
    result = parser.preprocess_groups(df).reset_index(drop=True)

    assert (
        result["dt"].tolist()
        == pd.to_datetime(["2024-01-01", "2024-01-01", "2024-01-02"]).tolist()
    )
    assert result["Product"].tolist() == ["Current", "Deposit", "Current"]


def test_preprocess_groups_stable_for_exact_ties():
    """Rows tied on both dt and Product must preserve original order."""
    df = pd.DataFrame(
        {
            "dt": pd.to_datetime(
                ["2024-01-01 09:22:22", "2024-01-01 09:22:22"]
            ),
            "Product": ["Current", "Current"],
            "Amount": ["first", "second"],
        }
    )
    parser = RevolutParser()
    result = parser.preprocess_groups(df).reset_index(drop=True)

    assert result["Amount"].tolist() == ["first", "second"]


def test_parse_writes_one_file_per_month(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    parser = RevolutParser()
    parser.parse(str(FIXTURE))

    output_files = sorted(f.name for f in tmp_path.glob("*.csv"))
    assert output_files == ["202401-revolut.csv", "202402-revolut.csv"]

    jan = pd.read_csv(tmp_path / "202401-revolut.csv")
    feb = pd.read_csv(tmp_path / "202402-revolut.csv")

    assert len(jan) == 4
    assert len(feb) == 2


def test_parse_splits_rows_into_correct_month_file(tmp_path, monkeypatch):
    """Row count alone doesn't catch a row landing in the wrong month."""
    monkeypatch.chdir(tmp_path)

    parser = RevolutParser()
    parser.parse(str(FIXTURE))

    jan = pd.read_csv(tmp_path / "202401-revolut.csv")
    feb = pd.read_csv(tmp_path / "202402-revolut.csv")

    assert set(jan["Completed Date"].str[:7]) == {"2024-01"}
    assert set(feb["Completed Date"].str[:7]) == {"2024-02"}


def test_parse_output_matches_original_schema(tmp_path, monkeypatch):
    """Written CSVs must exactly match the original export's column set,
    with no 'dt' leakage — this is the contract sync scripts rely on."""
    monkeypatch.chdir(tmp_path)

    parser = RevolutParser()
    parser.parse(str(FIXTURE))

    for f in tmp_path.glob("*.csv"):
        written = pd.read_csv(f)
        assert list(written.columns) == EXPECTED_COLUMNS

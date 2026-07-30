"""Tests for RevolutParser."""
# Written by AI.

from pathlib import Path

import pandas as pd
import pytest

from parse import REGISTRY
from parse.banks.revolut import RevolutParser

FIXTURE = Path(__file__).parent.joinpath("fixtures", "revolut_sample.csv")

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


def test_registry_returns_revolut_parser() -> None:
    """REGISTRY.get("revolut") resolves to a RevolutParser instance."""
    parser = REGISTRY.get("revolut")()
    assert isinstance(parser, RevolutParser)


def test_read_file_dt_matches_completed_date() -> None:
    """Dt must be a faithful parse of Completed Date, not just present."""
    parser = RevolutParser()
    df = parser.read_file(FIXTURE)

    expected = pd.to_datetime(df["Completed Date"], format="%Y-%m-%d %H:%M:%S")
    pd.testing.assert_series_equal(df["dt"], expected, check_names=False)


def test_read_file_numeric_columns_are_numeric() -> None:
    """Guards against decimal/thousands misparsing (as happened with CeptTEB)."""
    parser = RevolutParser()
    df = parser.read_file(FIXTURE)

    for col in ("Amount", "Fee", "Balance"):
        assert pd.api.types.is_float_dtype(df[col]), (
            f"{col} expected float dtype, got {df[col].dtype}"
        )


def test_read_file_preserves_original_schema() -> None:
    """Dt is an internal-only column; original export schema must be untouched.

    This is what allows downstream convert scripts to auto-detect export
    type by column signature.
    """
    parser = RevolutParser()
    df = parser.read_file(FIXTURE)

    assert [c for c in df.columns if c != "dt"] == EXPECTED_COLUMNS


def test_assert_path_wrong_extension_raises(tmp_path: Path) -> None:
    """A non-.csv file extension raises ValueError."""
    bad_file = tmp_path.joinpath("export.txt")
    bad_file.write_text("not a csv")

    parser = RevolutParser()
    with pytest.raises(ValueError, match="Unsupported file extension"):
        parser.assert_path(bad_file)


def test_assert_path_not_existing_file_raises(tmp_path: Path) -> None:
    """A non-existing file raises FileNotFoundError."""
    bad_file = tmp_path.joinpath("random.csv")

    parser = RevolutParser()
    with pytest.raises(FileNotFoundError, match="Path given does not exist"):
        parser.assert_path(bad_file)


def test_read_file_missing_required_column_raises(tmp_path: Path) -> None:
    """A CSV missing 'Completed Date' raises KeyError."""
    bad_csv = tmp_path.joinpath("broken.csv")
    bad_csv.write_text("Type,Product,Amount\nTransfer,Current,10.00\n")

    parser = RevolutParser()
    with pytest.raises(KeyError, match="Completed Date"):
        parser.read_file(bad_csv)


def test_read_file_empty_file_raises(tmp_path: Path) -> None:
    """A completely empty file raises pandas' EmptyDataError."""
    empty_csv = tmp_path / "empty.csv"
    empty_csv.write_text("")

    parser = RevolutParser()
    with pytest.raises(pd.errors.EmptyDataError):
        parser.read_file(empty_csv)


def test_parse_writes_one_file_per_month(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """parse() writes exactly one CSV per distinct month in the input."""
    monkeypatch.chdir(tmp_path)

    parser = RevolutParser()
    parser.parse(FIXTURE)

    output_files = sorted(f.name for f in tmp_path.glob("*.csv"))
    assert output_files == ["202401-revolut.csv", "202402-revolut.csv"]

    jan = pd.read_csv(tmp_path / "202401-revolut.csv")
    feb = pd.read_csv(tmp_path / "202402-revolut.csv")

    assert len(jan) == 4
    assert len(feb) == 2


def test_parse_splits_rows_into_correct_month_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Row count alone doesn't catch a row landing in the wrong month."""
    monkeypatch.chdir(tmp_path)

    parser = RevolutParser()
    parser.parse(FIXTURE)

    jan = pd.read_csv(tmp_path / "202401-revolut.csv")
    feb = pd.read_csv(tmp_path / "202402-revolut.csv")

    assert set(jan["Completed Date"].str[:7]) == {"2024-01"}
    assert set(feb["Completed Date"].str[:7]) == {"2024-02"}


def test_parse_output_matches_original_schema(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Assert written CSVs match the original export's column schema.

    This is the contract convert scripts rely on for auto-detecting export
    type by column signature, with no 'dt' leakage.
    """
    monkeypatch.chdir(tmp_path)

    parser = RevolutParser()
    parser.parse(FIXTURE)

    for f in tmp_path.glob("*.csv"):
        written = pd.read_csv(f)
        assert list(written.columns) == EXPECTED_COLUMNS

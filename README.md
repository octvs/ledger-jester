# ledger-jester

A stripped down fork of [ledger-autosync](github.com/egh/ledger-autosync).

## Dropped features

- `ofx` support
  - Refer to egh/ledger-autosync#141.
- `hledger` support
  - If there are users who can test against it, this can be added back.

## todo

- [ ] Add testing
  - [ ] Special test case: disregarded columns as in Amazon-Visa `Punkte`
        column
- [ ] Add ruff details to pyproject.toml
- [ ] We could also include functionality of the ledger-fx here

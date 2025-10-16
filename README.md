# ledger-jester

A stripped down fork of [ledger-autosync](github.com/egh/ledger-autosync).

## todo

- [ ] New converters
  - [ ] Enpara
- [ ] Merge w/ upstream
  - [ ] Find out how to merge w/ upstream by placing upstream components back
        into this repo, testing the newly implemented functionality along the
        way
- [ ] When payee names are set to the same cross accounts (ex. AmazonVisa and
      Revolut) dynamic payee names get jumbled. For example if how the name of
      "OASA" is seen are same for both, then it would appear as Amazon is
      paying to Revolut instaed of Expenses:Transportation.
  - We can circumvent this if we keep a reduced set of payee list for each
    account. Then this could be used for quick queries.

    Adding something like the following to a converter class might be
    considered
    ```python
    def initiate_direct_payees(self):
        _related = ["-l", f"any(account =~ /{self.name}/)"]
        _not_this = ["-l", f"not(account =~ /{self.name}/)"]
        r = self.lgr.run(["show", "--actual"] + _related + _not_this)
        for line in r:
            payee, account = line[2], line[3]
            if account == self.unknownaccount:
                continue
            if payee not in self.payees:
                self.direct_payees[payee] = []
            if account not in self.payees[payee]:
                self.direct_payees[payee].append(account)
    def mk_dynamic_account(self, payee, exclude):
        # if direct payee found return it
        # if not return the func from superclass (regular) as usual
        return super(AmazonVisaConverter, self).mk_dynamic_account(
            payee, exclude
        )
    ```

  - Another idea is to keep track of occurrence score while creating the payee
    list. This can be used to determine the best candidate with the
    `mk_dynamic_account`.
    - This might also help with the transactions which are always divided the
      same way for example the rent payment to "Herbert Vogel". If the
      occurrence is equal two accounts can be posted half and half. However
      this might cause much more issues to handle this edge case. For example
      "Tips" might occur as often as "Eating Out" for a single payee, and end
      up always showing.

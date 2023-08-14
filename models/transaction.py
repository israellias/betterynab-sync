class _BaseTransaction:
    def __init__(
        self,
        id,
        date,
        amount,
        memo,
        payee_id,
        payee_name,
        category_id,
        category_name,
        **ignored,
    ):
        self.id = id
        self.date = date
        self.amount = amount
        self.memo = memo
        self.payee_id = payee_id
        self.payee_name = payee_name
        self.category_id = category_id
        self.category_name = category_name

    @property
    def identifier(self) -> str:
        """
        each transaction could have a identifier in its memo that is write like
        `abcd1234-1008` that indicates the transaction (on other budget) that
        this transaction represents
        """
        return "{}|{}".format(self.id[:8], "".join(self.date.split("-")[1:]))

    @property
    def memo_identifier(self) -> str:
        return self.memo and self.memo.strip()[-13:]

    def __eq__(self, _value: object) -> bool:
        if not issubclass(_value.__class__, _BaseTransaction):
            return False

        return (
            self.identifier == _value.memo_identifier
            or self.memo_identifier == _value.identifier
        )


class Subtransaction(_BaseTransaction):
    pass


class Transaction(_BaseTransaction):
    def __init__(
        self,
        cleared,
        approved,
        flag_color,
        account_id,
        account_name,
        transfer_account_id,
        transfer_transaction_id,
        matched_transaction_id,
        deleted,
        subtransactions,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.cleared = cleared
        self.approved = approved
        self.flag_color = flag_color
        self.account_id = account_id
        self.account_name = account_name
        self.transfer_account_id = transfer_account_id
        self.transfer_transaction_id = transfer_transaction_id
        self.matched_transaction_id = matched_transaction_id
        self.deleted = deleted
        self.subtransactions = [
            subtransaction
            if isinstance(subtransaction, Subtransaction)
            else Subtransaction(**subtransaction, date=self.date)
            for subtransaction in subtransactions
        ]

    def __str__(self):
        return f"{self.date} {self.category_name} {self.amount}"

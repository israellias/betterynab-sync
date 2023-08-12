class Subtransaction:
    def __init__(
        self,
        id,
        amount,
        memo,
        payee_id,
        payee_name,
        category_id,
        category_name,
        **ignored,
    ):
        self.id = id
        self.amount = amount
        self.memo = memo
        self.payee_id = payee_id
        self.payee_name = payee_name
        self.category_id = category_id
        self.category_name = category_name


class Transaction:
    def __init__(
        self,
        id,
        date,
        amount,
        memo,
        cleared,
        approved,
        flag_color,
        account_id,
        account_name,
        payee_id,
        payee_name,
        category_id,
        category_name,
        transfer_account_id,
        transfer_transaction_id,
        matched_transaction_id,
        deleted,
        subtransactions,
        **ignored,
    ):
        self.id = id
        self.date = date
        self.amount = amount
        self.memo = memo
        self.cleared = cleared
        self.approved = approved
        self.flag_color = flag_color
        self.account_id = account_id
        self.account_name = account_name
        self.payee_id = payee_id
        self.payee_name = payee_name
        self.category_id = category_id
        self.category_name = category_name
        self.transfer_account_id = transfer_account_id
        self.transfer_transaction_id = transfer_transaction_id
        self.matched_transaction_id = matched_transaction_id
        self.deleted = deleted
        self.subtransactions = [
            subtransaction
            if isinstance(subtransaction, Subtransaction)
            else Subtransaction(**subtransaction)
            for subtransaction in subtransactions
        ]

    def __str__(self):
        return f"{self.date} {self.category_name} {self.amount}"

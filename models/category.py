from models import Transaction


class Category:
    def __init__(
        self,
        id,
        category_group_id,
        category_group_name,
        name,
        hidden,
        note,
        budgeted,
        activity,
        balance,
        deleted,
        **ignored,
    ):
        self.id = id
        self.category_group_id = category_group_id
        self.category_group_name = category_group_name
        self.name: str = name
        self.hidden = hidden
        self.note = note
        self.budgeted = budgeted
        self.activity = activity
        self.balance = balance
        self.deleted = deleted
        self.transactions: [Transaction] = []

    def __str__(self) -> str:
        return f"{self.name} ({self.balance})"

    def __repr__(self) -> str:
        return f"{self.name} ({self.balance})"

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, Category):
            return False
        return self.id == o.id

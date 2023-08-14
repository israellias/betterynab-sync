from os import environ as env

from models import Transaction, Subtransaction, Budget, Category


class CreateTransactionInterface:
    def __init__(
        self,
        account_id,
        date,
        amount,
        category_id,
        payee_name=None,
        memo=None,
        cleared=None,
        approved=None,
        flag_color=None,
    ):
        self.account_id = account_id
        self.date = date
        self.amount = amount
        self.category_id = category_id
        self.payee_name = payee_name
        self.memo = memo
        self.cleared = cleared
        self.approved = approved
        self.flag_color = flag_color

    @classmethod
    def from_transaction(
        cls,
        budget: Budget,
        transaction: Transaction,
        main_budget_categories: list[Category],
    ):
        return cls(
            account_id=cls._account_id(budget),
            date=transaction.date,
            amount=transaction.amount,
            category_id=cls._category_id(
                main_budget_categories,
                transaction.category_name,
            ),
            payee_name=cls._payee_name(transaction.payee_name),
            memo=cls._memo(transaction),
            cleared="cleared",
            approved=True,
            flag_color=transaction.flag_color,
        )

    @classmethod
    def from_subtransaction(
        cls,
        budget: Budget,
        transaction: Transaction,
        subtransaction: Subtransaction,
        main_budget_categories: list[Category],
    ):
        return cls(
            account_id=cls._account_id(budget),
            date=transaction.date,
            amount=subtransaction.amount,
            category_id=cls._category_id(
                main_budget_categories,
                subtransaction.category_name,
            ),
            payee_name=cls._payee_name(subtransaction.payee_name),
            memo=cls._memo(subtransaction),
            cleared="cleared",
            approved=True,
            flag_color=transaction.flag_color,
        )

    @staticmethod
    def _account_id(budget: Budget):
        if budget.name == "BOB Budget":
            account_id = env.get("BOB_BUDGET_ACCOUNT")
        elif budget.name == "ARS Budget":
            account_id = env.get("ARS_BUDGET_ACCOUNT")
        else:
            account_id = None

        return account_id

    @staticmethod
    def _category_id(main_budget_categories: list[Category], category_name: str):
        for category in main_budget_categories:
            if category.name.strip() == category_name.strip():
                return category.id
        return None

    @staticmethod
    def _memo(transaction):
        return "{} {}".format(transaction.memo, transaction.identifier)

    @staticmethod
    def _payee_name(payee_name):
        if payee_name is not None and (
            payee_name.startswith("Transfer :")
            or payee_name.startswith("Starting Balance")
            or payee_name.startswith("Manual Balance Adjustment")
            or payee_name.startswith("Reconciliation Balance Adjustment")
        ):
            return None
        return payee_name

    def to_dict(self):
        return {
            "account_id": self.account_id,
            "date": self.date,
            "amount": self.amount,
            "payee_name": self.payee_name,
            "category_id": self.category_id,
            "memo": self.memo,
            "cleared": self.cleared,
            "approved": self.approved,
            "flag_color": self.flag_color,
        }

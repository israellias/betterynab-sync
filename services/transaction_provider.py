from functools import reduce
from os import environ as env

from models import Budget
from services._ynab_connection import YNABClient, CreateTransactionInterface


def _process_transactions(
    budget: Budget, main_budget: Budget
) -> [CreateTransactionInterface]:
    create_transactions = []

    def parse_main_transactions(acc, t):
        if t.account_id not in (
            env.get("BOB_BUDGET_ACCOUNT"),
            env.get("ARS_BUDGET_ACCOUNT"),
        ):
            return acc  # Skip
        if t.subtransactions:
            acc.extend(t.subtransactions)
        else:
            acc.append(t)
        return acc

    main_budget_transactions = reduce(
        parse_main_transactions, main_budget.transactions, []
    )

    for transaction in budget.transactions:
        # Check if transaction has subtransations
        if transaction.subtransactions:
            for subtransaction in transaction.subtransactions:
                if (
                    "⚙️" in subtransaction.category_name
                    or "Transfer :" in (subtransaction.payee_name or "")
                    or subtransaction in main_budget_transactions
                ):  # calls the __eq__ method for CreateTransactionInterface
                    continue

                create_transactions.append(
                    CreateTransactionInterface.from_subtransaction(
                        budget=budget,
                        transaction=transaction,
                        subtransaction=subtransaction,
                        main_budget_categories=main_budget.categories,
                        main_budget_transactions=main_budget_transactions,
                    )
                )
        else:
            if (
                "⚙️" in transaction.category_name
                or "Transfer :" in (transaction.payee_name or "")
                or transaction in main_budget_transactions
            ):  # calls the __eq__ method for CreateTransactionInterface
                continue

            create_transactions.append(
                CreateTransactionInterface.from_transaction(
                    budget=budget,
                    transaction=transaction,
                    main_budget_categories=main_budget.categories,
                    main_budget_transactions=main_budget_transactions,
                )
            )

    return create_transactions


def sync_transactions_to_main_budget(budget: Budget, main_budget: Budget):
    """
    Check which new transactions needs to be written on the main_budget
    """

    print("Checking for new transactions... on budget", budget.name)

    create_transactions = _process_transactions(budget, main_budget)

    for transaction in create_transactions:
        YNABClient().create_transaction(main_budget.id, transaction.to_dict())

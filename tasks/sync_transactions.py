from services import (
    relevant_budgets,
    fill_transactions,
    sync_transactions_to_main_budget,
)


def sync_transactions(only_credit_card=False, since_date=None):
    """Sync transactions from one budget to another

    Args:
        only_credit_card: If True, sync only BISA credit card transactions.
                         If False (default), sync all except credit card.
        since_date: Start date for syncing (YYYY-MM-DD format). Required.
    """

    # Get budgets
    main_budget, sync_budgets = relevant_budgets()

    # Get main budget transactions
    main_budget = fill_transactions(main_budget, since_date)

    # Get sync budgets transactions
    sync_budgets = [fill_transactions(budget, since_date) for budget in sync_budgets]

    # Check for new transactions
    for sync_budget in sync_budgets:
        sync_transactions_to_main_budget(sync_budget, main_budget, only_credit_card)

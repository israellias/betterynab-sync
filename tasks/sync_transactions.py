from services import (
    relevant_budgets,
    fill_transactions,
    sync_transactions_to_main_budget,
)


def sync_transactions_to_main_budget():
    """Sync transactions from one budget to another"""

    # Get budgets
    main_budget, sync_budgets = relevant_budgets()

    # Get main budget transactions
    main_budget = fill_transactions(main_budget)

    # Get sync budgets transactions
    sync_budgets = [fill_transactions(budget) for budget in sync_budgets]

    # Check for new transactions
    for sync_budget in sync_budgets:
        sync_transactions_to_main_budget(sync_budget, main_budget)

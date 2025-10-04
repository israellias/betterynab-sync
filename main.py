# Just run a quick command that execute a sum with no params
# and print the result


from tasks.sync_transactions import sync_transactions
from tasks.sync_categories import sync_categories

from dotenv import load_dotenv

load_dotenv()

if __name__ == "__main__":
    sync_transactions()
    # sync_categories()

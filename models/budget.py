from models import Category, Transaction


class CurrencyFormat:
    def __init__(
        self,
        iso_code,
        example_format,
        decimal_digits,
        decimal_separator,
        symbol_first,
        group_separator,
        currency_symbol,
        display_symbol,
        **ignored,
    ):
        self.iso_code = iso_code
        self.example_format = example_format
        self.decimal_digits = decimal_digits
        self.decimal_separator = decimal_separator
        self.symbol_first = symbol_first
        self.group_separator = group_separator
        self.currency_symbol = currency_symbol
        self.display_symbol = display_symbol


class Budget:
    def __init__(self, id, name, last_modified_on, currency_format, **ignored):
        self.id = id
        self.name = name
        self.last_modified_on = last_modified_on
        self.currency_format = CurrencyFormat(**currency_format)
        self.categories: list[Category] = []
        self.uncategorized_transactions: list[Transaction] = []

    @property
    def transactions(self):
        return [
            transaction
            for category in self.categories
            for transaction in category.transactions
        ] + self.uncategorized_transactions

    def assign_categories(self, categories):
        self.categories = [
            category if isinstance(category, Category) else Category(**category)
            for category in categories
        ]
        return self

    def assign_transactions(self, transactions):
        for transaction in transactions:
            category = next(
                (
                    category
                    for category in self.categories
                    if category.id == transaction.category_id
                ),
                None,
            )
            if category:
                category.transactions.append(transaction)
            else:
                self.uncategorized_transactions.append(transaction)

        return self

    def __str__(self) -> str:
        return f"{self.name} ({self.currency_format.iso_code})"

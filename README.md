# betterynab-sync

## Main Goal

When you get your main income in a single currency and/or you intent to use a single currency to leave money there. But you are spending money in different currencies then you get trouble syncing this expenses in both currencies.

The problem increases its complexity when volatity on exchange rates is present. That leads you to not know how many (in local) money could you expend e.g. the last week of the month.

So the main goal is to handle budgets that occur in different currencies but, at the same time, get their incomes from the same source (This is the main budget)

# Explanation

You could use your **main budget** for:

- Assign money for all your categories (even those that has their transactions in other currency).

You could use your **second budgets** for:

- Register money in your local currency and this will create a transaction in your main budget applying the current exchange rate. Which indicates the real cost of everything you're expending.

Finally you could pay attention on a single budget (the main one) and start increasing the Age of Money and see relevant reports on how much you're expending and in what.

## How to use

Run the script every single day at the end of the day.

```bash
$ python main.py
```

### Preconditions

Some considerations

1. Your categories (of the main budget) needs to be present in all the
   other budgets (have the same name)
1. Transactions of a category that has "⚙️" will be ignored
1. You must have an **account** in the main budget that have the same name that your secondary budget has. That means, one account per each secondary budget

### Restrictions

At this moment you only can use this names

- USD Budget
- BOB Budget
- ARS Budget

the first one is the main budget

## Contributions

## How to test

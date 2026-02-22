# BISA Transaction Rules

Rules for auto-categorizing BISA debit account transactions.

## Credit Card Payment Rules

When a transaction memo matches these patterns, assign payee to "BISA CC" Transfer account.

- Pago automatico tarj. credito
- Débito Pago Tarjeta Crédito
- Anticipo Tarj. Crédito eBISA

## Amount-Based Rules

For `SYSPago` transactions (automated loan payments), categorize by amount range:

| Pattern (in memo) | Amount Range (BOB) | Payee | Category |
|---|---|---|---|
| SYSPago | 8000 - 10000 | BCP | Hipoteca |
| SYSPago | 2000 - 3000 | BCP | Préstamo Vehicular |

## AI Guidance

For transactions not matched by rules above:
- POS transactions (DEBITO POR COMPRA POS) with merchant-looking names are usually stores
- TRASP.CTAS.TERCEROS are bank transfers to people
- Always try to extract a payee name from the memo for better matching and reporting, even if it's not in the rules

import json
from datetime import datetime
from decimal import Decimal


class BinanceConverter:
    def convert(self, json_path: str, account_id: str, transfer_payee_id: str) -> list:
        """Parse Binance P2P JSON and return YNAB API transaction dicts.

        Filters: orderStatus == 4 (completed), tradeType == "SELL", fiat == "BOB".
        """
        with open(json_path, "r") as f:
            data = json.load(f)

        orders = data.get("data", [])
        filtered = [
            o for o in orders
            if o.get("orderStatus") == 4
            and o.get("tradeType") == "SELL"
            and o.get("fiat") == "BOB"
        ]

        transactions = []
        for order in filtered:
            amount = Decimal(order["amount"])
            total_price = Decimal(order["totalPrice"])
            price = Decimal(order["price"])
            username = order.get("buyerNickname", "")
            order_number = order["orderNumber"]
            iso_date = datetime.fromtimestamp(
                order["createTime"] / 1000
            ).strftime("%Y-%m-%d")

            memo = (
                f"[TC:{self._fmt(price)}] "
                f"SELL {self._fmt(amount)} USDT "
                f"with {self._fmt(total_price)} BOB ({username})"
            )

            transactions.append({
                "account_id": account_id,
                "date": iso_date,
                "amount": int(-amount * 1000),
                "payee_id": transfer_payee_id,
                "memo": memo,
                "cleared": "cleared",
                "approved": True,
                "import_id": f"BNCP2P:{order_number[:10]}:{iso_date}",
            })

        return transactions

    @staticmethod
    def _fmt(value: Decimal) -> str:
        """Format decimal: 2 decimal places for typical currencies."""
        return str(round(float(value), 2))

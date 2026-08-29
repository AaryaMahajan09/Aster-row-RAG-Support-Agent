import json
from pathlib import Path
from typing import Optional, Dict, Any


class OrderLookup:

    def __init__(self, orders_path: str):

        self.orders_path = Path(orders_path)

        with self.orders_path.open(
            "r",
            encoding="utf-8"
        ) as file:
            data = json.load(file)

        # The JSON contains metadata at the top level
        # and the actual orders inside the "orders" list.
        self.orders = data["orders"]

        # Create a fast lookup dictionary.
        self.orders_by_id = {
            order["order_id"].upper(): order
            for order in self.orders
        }

    def normalize_order_id(
        self,
        order_id: str
    ) -> str:
        """
        Normalize the order ID.

        Example:
            ord-1007 -> ORD-1007
        """

        return order_id.strip().upper()

    def lookup_order(
        self,
        order_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Look up an order by its order ID.

        This method returns the raw internal record.
        It should only be used internally.
        """

        normalized_id = self.normalize_order_id(
            order_id
        )

        return self.orders_by_id.get(
            normalized_id
        )

    def get_customer_safe_order(
        self,
        order_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Return only customer-safe information.

        Sensitive customer information and internal
        operational information are deliberately excluded.
        """

        order = self.lookup_order(order_id)

        if order is None:
            return None

        safe_items = []

        for item in order.get("items", []):

            safe_items.append({
                "name": item.get("name"),
                "quantity": item.get("quantity"),
                "final_sale": item.get("final_sale")
            })

        safe_order = {
            "order_id": order.get("order_id"),
            "membership_tier": order.get("membership_tier"),
            "items": safe_items,
            "placed_at": order.get("placed_at"),
            "status": order.get("status"),
            "status_updated_at": order.get(
                "status_updated_at"
            ),
            "shipped_at": order.get("shipped_at"),
            "delivered_at": order.get("delivered_at"),
            "carrier": order.get("carrier"),
            "tracking_number": order.get(
                "tracking_number"
            ),
            "estimated_delivery": order.get(
                "estimated_delivery"
            ),
            "customer_safe_message": order.get(
                "customer_safe_message"
            )
        }

        return safe_order

    def get_order_status_summary(
        self,
        order_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Return a customer-safe summary of the order status.

        This method applies deterministic rules so that the
        language model does not have to interpret sensitive
        or contradictory order fields itself.
        """

        order = self.get_customer_safe_order(order_id)

        if order is None:
            return None

        status = order["status"]

        result = {
            "order_id": order["order_id"],
            "status": status,
            "items": order["items"],
            "message": "",
            "carrier": None,
            "tracking_number": None,
            "estimated_delivery": None,
            "handoff_recommended": False
        }

        # -----------------------------
        # PENDING
        # -----------------------------
        if status == "pending":

            result["message"] = (
                order["customer_safe_message"]
                or "Your order has been received and is being processed."
            )

        # -----------------------------
        # PROCESSING
        # -----------------------------
        elif status == "processing":

            result["message"] = (
                order["customer_safe_message"]
                or "Your order is currently being processed."
            )

        # -----------------------------
        # SHIPPED
        # -----------------------------
        elif status == "shipped":

            result["carrier"] = order["carrier"]
            result["tracking_number"] = order["tracking_number"]

            result["message"] = (
                order["customer_safe_message"]
                or "Your order has shipped."
            )

            # Only expose ETA if one actually exists.
            if order["estimated_delivery"]:

                result["estimated_delivery"] = (
                    order["estimated_delivery"]
                )

        # -----------------------------
        # DELIVERED
        # -----------------------------
        elif status == "delivered":

            result["message"] = (
                order["customer_safe_message"]
                or "Your order has been delivered."
            )

        # -----------------------------
        # CANCELLED
        # -----------------------------
        elif status == "cancelled":

            # IMPORTANT:
            # Ignore any stale estimated_delivery value.
            result["estimated_delivery"] = None

            result["message"] = (
                order["customer_safe_message"]
                or "Your order has been cancelled."
            )

        # -----------------------------
        # EXCEPTION
        # -----------------------------
        elif status == "exception":

            result["message"] = (
                order["customer_safe_message"]
                or "There is an issue with your order."
            )

            result["handoff_recommended"] = True

        # -----------------------------
        # UNKNOWN STATUS
        # -----------------------------
        else:

            result["message"] = (
                order["customer_safe_message"]
                or "Your order status is currently unavailable."
            )

            result["handoff_recommended"] = True

        return result


if __name__ == "__main__":

    order_lookup = OrderLookup(
        "data/orders.json"
    )

    test_id = "ORD-1010"

    order = order_lookup.lookup_order(
        test_id
    )

    print("Order found:")
    print(order is not None)

    print("\nCustomer-safe order:")

    status_summary = order_lookup.get_order_status_summary(
        test_id
    )

    print(status_summary)
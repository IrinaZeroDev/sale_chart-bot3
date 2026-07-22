from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
from .models import Lead


PRODUCTS = [
    {"id": "PRD-101", "name": "Business Start", "price": 49_900, "currency": "RUB", "lead_time_days": 5, "available": True, "description": "Базовый пакет автоматизации продаж"},
    {"id": "PRD-202", "name": "Business Pro", "price": 89_900, "currency": "RUB", "lead_time_days": 10, "available": True, "description": "Автоматизация продаж с интеграцией CRM"},
    {"id": "PRD-303", "name": "Enterprise", "price": None, "currency": "RUB", "lead_time_days": 20, "available": True, "description": "Индивидуальное решение для корпоративных систем"},
]

ORDERS = {
    "ORD-1001": {"order_id": "ORD-1001", "status": "В обработке", "product": "Business Start", "updated_at": "2026-07-21T12:30:00+03:00", "estimated_delivery": "2026-07-25"},
    "ORD-1002": {"order_id": "ORD-1002", "status": "Передан в доставку", "product": "Business Pro", "updated_at": "2026-07-22T09:15:00+03:00", "estimated_delivery": "2026-07-24"},
    "ORD-1003": {"order_id": "ORD-1003", "status": "Выполнен", "product": "Business Start", "updated_at": "2026-07-18T16:00:00+03:00", "estimated_delivery": "2026-07-18"},
}


class MockCompanySystem:
    """Реалистичная in-memory заглушка каталога, заказов, CRM и аналитики."""

    def __init__(self):
        self.products = deepcopy(PRODUCTS)
        self.orders = deepcopy(ORDERS)
        self.leads: list[dict] = []
        self.events: list[dict] = []

    def list_products(self) -> list[dict]:
        return self.products

    def find_products(self, query: str) -> list[dict]:
        words = set(query.lower().replace("-", " ").split())
        matches = [p for p in self.products if words & set((p["id"] + " " + p["name"] + " " + p["description"]).lower().replace("-", " ").split())]
        return matches or self.products

    def get_order(self, order_id: str) -> dict | None:
        return self.orders.get(order_id.upper())

    async def send(self, lead: Lead) -> None:
        self.leads.append({
            "lead_id": f"LEAD-{len(self.leads) + 1:04d}",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "status": "new",
            **lead.model_dump(),
        })

    def track(self, session_id: str, topic: str, handoff: bool = False) -> None:
        self.events.append({"session_id": session_id, "topic": topic, "handoff": handoff})

    def metrics(self) -> dict:
        sessions = {event["session_id"] for event in self.events}
        topics = Counter(event["topic"] for event in self.events)
        return {
            "dialogs": len(sessions),
            "messages": len(self.events),
            "leads": len(self.leads),
            "conversion_percent": round(len(self.leads) / len(sessions) * 100, 1) if sessions else 0.0,
            "handoffs": sum(event["handoff"] for event in self.events),
            "popular_topics": dict(topics.most_common()),
        }


import re
from dataclasses import dataclass, field
from .models import ChatRequest, ChatResponse, Lead
from .providers import LLMProvider

GREETING = "Здравствуйте. Чем могу помочь: информация о товарах, статус заказа или вопросы поддержки?"
SYSTEM_PROMPT = """Вы — консультант отдела продаж. Отвечайте на русском языке профессионально, вежливо и лаконично.
Используйте только факты из переданного контекста. Не придумывайте цены, сроки, статусы и условия.
Если данных недостаточно, прямо сообщите об этом и предложите передачу менеджеру. Не оказывайте давления.
Контакт можно сохранять только после явного согласия. Никогда не запрашивайте паспорт, банковскую карту или пароль."""
ORDER_RE = re.compile(r"(?:ORD[-\s]?)?\d{4,}", re.IGNORECASE)
CONTACT_RE = re.compile(r"(?:\+?\d[\d\s()\-]{8,}\d)|(?:[\w.+-]+@[\w.-]+\.[A-Za-zА-Яа-я]{2,})")
HUMAN_WORDS = ("оператор", "менеджер", "человек", "жалоба", "не помог")


@dataclass
class Session:
    stage: str = "menu"
    messages: list[dict[str, str]] = field(default_factory=list)
    need: str | None = None
    consent: bool = False


class DialogService:
    def __init__(self, provider: LLMProvider, company):
        self.provider = provider
        self.company = company
        self.sessions: dict[str, Session] = {}

    def response(self, request: ChatRequest, reply: str, stage: str, topic: str, *, handoff=False, lead_created=False):
        self.company.track(request.session_id, topic, handoff)
        return ChatResponse(session_id=request.session_id, reply=reply, stage=stage, handoff=handoff, lead_created=lead_created)

    async def reply(self, request: ChatRequest) -> ChatResponse:
        session = self.sessions.setdefault(request.session_id, Session())
        text, lower = request.message.strip(), request.message.strip().lower()
        command = lower.split(maxsplit=1)[0]
        if request.consent_to_contact is not None:
            session.consent = request.consent_to_contact

        if command in {"/start", "/menu"} or lower in {"start", "начать", "привет", "здравствуйте", "меню"}:
            session.stage = "menu"
            return self.response(request, GREETING, session.stage, "menu")

        if command == "/products":
            text, lower = "Покажите товары и цены", "товары цены"
        elif command == "/order":
            order_argument = text[len(command):].strip()
            text = f"Статус заказа {order_argument}" if order_argument else "Статус заказа"
            lower = text.lower()
        elif command == "/support":
            text, lower = "Вопросы поддержки", "поддержка"
        elif command == "/manager":
            text, lower = "Позовите менеджера", "менеджер"

        if any(word in lower for word in HUMAN_WORDS):
            session.stage = "handoff"
            return self.response(request, "Ваше обращение будет передано менеджеру. Для обратной связи подтвердите согласие и укажите телефон или email.", session.stage, "handoff", handoff=True)

        contact = CONTACT_RE.search(text)
        if contact:
            if not session.consent:
                return self.response(request, "Контакт не будет сохранён без вашего согласия. Подтвердите, пожалуйста, согласие на обработку контактных данных для обратной связи.", "consent", "lead")
            await self.company.send(Lead(session_id=request.session_id, contact=contact.group(0), need=session.need, channel=request.channel, consent=True))
            session.stage = "qualified"
            return self.response(request, "Благодарю. Заявка зарегистрирована и передана менеджеру.", session.stage, "lead", lead_created=True)

        if "статус" in lower or "заказ" in lower or ORDER_RE.search(text):
            match = ORDER_RE.search(text)
            if not match:
                session.stage = "order_lookup"
                return self.response(request, "Укажите, пожалуйста, номер заказа в формате ORD-1001.", session.stage, "order_status")
            digits = re.sub(r"\D", "", match.group(0))
            order = self.company.get_order(f"ORD-{digits}")
            if not order:
                return self.response(request, "Заказ с указанным номером не найден. Проверьте номер или запросите помощь менеджера.", "order_lookup", "order_status")
            reply = f"Заказ {order['order_id']}: {order['status']}. Ориентировочная дата выполнения — {order['estimated_delivery']}."
            return self.response(request, reply, "order_found", "order_status")

        if any(word in lower for word in ("товар", "продукт", "цен", "стоимость", "прайс", "business", "enterprise")):
            products = self.company.find_products(text)
            lines = []
            for product in products:
                price = f"{product['price']:,} ₽".replace(",", " ") if product["price"] else "по индивидуальному расчёту"
                lines.append(f"{product['name']} — {price}; срок выполнения от {product['lead_time_days']} дней")
            session.need = text
            return self.response(request, "Доступные предложения:\n" + "\n".join(lines), "products", "products")

        if any(word in lower for word in ("достав", "срок", "оплат", "возврат", "поддерж")):
            if "достав" in lower:
                answer = "Доставка выполняется по России после подтверждения заказа. Точный способ, стоимость и дата рассчитываются при оформлении."
            elif "срок" in lower:
                answer = "Стандартный срок выполнения зависит от продукта: от 5 дней для Business Start, от 10 дней для Business Pro и от 20 дней для Enterprise."
            elif "оплат" in lower:
                answer = "Оплата производится по счёту после подтверждения состава заказа. Индивидуальные условия согласовываются с менеджером."
            elif "возврат" in lower:
                answer = "Условия возврата зависят от состава заказа и договора. Передам вопрос менеджеру, чтобы не сообщать неподтверждённые условия."
            else:
                answer = "Уточните, пожалуйста, вопрос: доставка, оплата, сроки выполнения или возврат."
            return self.response(request, answer, "support", "support", handoff="возврат" in lower)

        session.need = session.need or text
        answer = await self.provider.complete([{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": text}])
        return self.response(request, answer + " Если необходим точный ответ, обращение можно передать менеджеру.", "fallback", "other")

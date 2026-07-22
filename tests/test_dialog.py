import pytest
from app.company_system import MockCompanySystem
from app.dialog import DialogService, GREETING
from app.models import ChatRequest
from app.providers import MockProvider


@pytest.fixture
def service():
    company = MockCompanySystem()
    return DialogService(MockProvider(), company), company


@pytest.mark.asyncio
async def test_professional_menu(service):
    bot, _ = service
    result = await bot.reply(ChatRequest(session_id="1", message="/start"))
    assert result.reply == GREETING


@pytest.mark.asyncio
async def test_product_prices_from_catalog(service):
    bot, _ = service
    result = await bot.reply(ChatRequest(session_id="2", message="Какие цены на продукты?"))
    assert "49 900 ₽" in result.reply and "Business Pro" in result.reply


@pytest.mark.asyncio
async def test_order_status(service):
    bot, _ = service
    result = await bot.reply(ChatRequest(session_id="3", message="Статус заказа ORD-1002"))
    assert "Передан в доставку" in result.reply


@pytest.mark.asyncio
async def test_unknown_order_does_not_guess(service):
    bot, _ = service
    result = await bot.reply(ChatRequest(session_id="4", message="Статус заказа 9999"))
    assert "не найден" in result.reply


@pytest.mark.asyncio
async def test_contact_requires_consent(service):
    bot, company = service
    result = await bot.reply(ChatRequest(session_id="5", message="user@example.com"))
    assert result.stage == "consent" and not company.leads


@pytest.mark.asyncio
async def test_lead_and_metrics(service):
    bot, company = service
    result = await bot.reply(ChatRequest(session_id="6", message="user@example.com", consent_to_contact=True))
    assert result.lead_created and company.leads[0]["lead_id"] == "LEAD-0001"
    assert company.metrics()["conversion_percent"] == 100.0

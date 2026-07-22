import logging
import httpx
from fastapi import Depends, FastAPI, Header, HTTPException
from .config import Settings, get_settings
from .dialog import DialogService
from .company_system import MockCompanySystem
from .models import ChatRequest, ChatResponse, HealthResponse
from .providers import build_provider

logging.basicConfig(level=logging.INFO)
settings = get_settings()
company = MockCompanySystem()
dialog = DialogService(build_provider(settings), company)
app = FastAPI(title="Sales Chat Bot API", version="1.0.0")


def verify_api_key(x_api_key: str = Header(default=""), cfg: Settings = Depends(get_settings)) -> None:
    if cfg.internal_api_key and x_api_key != cfg.internal_api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(provider=settings.llm_provider)


@app.post("/api/v1/chat", response_model=ChatResponse, dependencies=[Depends(verify_api_key)])
async def chat(request: ChatRequest) -> ChatResponse:
    try:
        return await dialog.reply(request)
    except httpx.HTTPError:
        logging.exception("Upstream service failed")
        raise HTTPException(status_code=502, detail="AI or CRM service is temporarily unavailable")


@app.get("/api/v1/demo/products", dependencies=[Depends(verify_api_key)])
async def products():
    return {"items": company.list_products()}


@app.get("/api/v1/demo/orders/{order_id}", dependencies=[Depends(verify_api_key)])
async def order(order_id: str):
    item = company.get_order(order_id)
    if not item:
        raise HTTPException(status_code=404, detail="Order not found")
    return item


@app.get("/api/v1/demo/leads", dependencies=[Depends(verify_api_key)])
async def leads():
    return {"items": company.leads}


@app.get("/api/v1/metrics", dependencies=[Depends(verify_api_key)])
async def metrics():
    return company.metrics()

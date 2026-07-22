import logging
import httpx
import mimetypes
from collections import defaultdict, deque
from pathlib import Path
from time import monotonic
from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from .config import Settings, get_settings
from .dialog import DialogService
from .company_system import MockCompanySystem
from .models import ChatRequest, ChatResponse, HealthResponse
from .providers import build_provider

logging.basicConfig(level=logging.INFO)
mimetypes.add_type("application/javascript", ".js")
mimetypes.types_map[".js"] = "application/javascript"
settings = get_settings()
company = MockCompanySystem()
dialog = DialogService(build_provider(settings), company)
app = FastAPI(title="Sales Chat Bot API", version="1.0.0")
static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")
public_requests: dict[str, deque[float]] = defaultdict(deque)


def verify_api_key(x_api_key: str = Header(default=""), cfg: Settings = Depends(get_settings)) -> None:
    if cfg.internal_api_key and x_api_key != cfg.internal_api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(provider=settings.llm_provider)


@app.get("/", include_in_schema=False)
async def web_app():
    return FileResponse(static_dir / "index.html")


@app.post("/api/v1/public/chat", response_model=ChatResponse)
async def public_chat(request: ChatRequest, http_request: Request) -> ChatResponse:
    client_id = http_request.client.host if http_request.client else "unknown"
    now = monotonic()
    timestamps = public_requests[client_id]
    while timestamps and now - timestamps[0] > 60:
        timestamps.popleft()
    if len(timestamps) >= 30:
        raise HTTPException(status_code=429, detail="Слишком много запросов. Повторите через минуту.")
    timestamps.append(now)
    return await chat(request)


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

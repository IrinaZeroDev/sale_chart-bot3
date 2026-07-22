import httpx
from .config import Settings
from .models import Lead


class LeadSink:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.memory: list[Lead] = []

    async def send(self, lead: Lead) -> None:
        self.memory.append(lead)
        if not self.settings.crm_webhook_url:
            return
        headers = {"Authorization": f"Bearer {self.settings.crm_webhook_token}"} if self.settings.crm_webhook_token else {}
        async with httpx.AsyncClient(timeout=self.settings.request_timeout) as client:
            response = await client.post(self.settings.crm_webhook_url, json=lead.model_dump(), headers=headers)
            response.raise_for_status()


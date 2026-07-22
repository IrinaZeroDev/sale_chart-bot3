import express from 'express';

export function createApp({ fetchImpl = fetch } = {}) {
  const app = express();
  app.use(express.json({ limit: '32kb' }));
  app.get('/health', (_req, res) => res.json({ status: 'ok' }));
  app.post('/webhook/messages', async (req, res) => {
    const { sessionId, message, channel = 'web', consentToContact } = req.body ?? {};
    if (typeof sessionId !== 'string' || typeof message !== 'string' || !message.trim()) {
      return res.status(400).json({ error: 'sessionId and message are required' });
    }
    try {
      const upstream = await fetchImpl(`${process.env.PYTHON_API_URL ?? 'http://localhost:8000'}/api/v1/chat`, {
        method: 'POST',
        headers: { 'content-type': 'application/json', 'x-api-key': process.env.INTERNAL_API_KEY ?? 'change-me' },
        body: JSON.stringify({ session_id: sessionId, message, channel, consent_to_contact: consentToContact })
      });
      const body = await upstream.json();
      return res.status(upstream.status).json(body);
    } catch {
      return res.status(502).json({ error: 'Chat service is unavailable' });
    }
  });
  app.post('/webhook/telegram', async (req, res) => {
    const expectedSecret = process.env.TELEGRAM_WEBHOOK_SECRET;
    if (expectedSecret && req.get('x-telegram-bot-api-secret-token') !== expectedSecret) {
      return res.status(401).json({ error: 'Invalid webhook secret' });
    }
    const message = req.body?.message;
    if (!message?.chat?.id || typeof message.text !== 'string') return res.sendStatus(200);
    try {
      const upstream = await fetchImpl(`${process.env.PYTHON_API_URL ?? 'http://localhost:8000'}/api/v1/chat`, {
        method: 'POST',
        headers: { 'content-type': 'application/json', 'x-api-key': process.env.INTERNAL_API_KEY ?? 'change-me' },
        body: JSON.stringify({ session_id: String(message.chat.id), message: message.text, channel: 'telegram' })
      });
      const answer = await upstream.json();
      if (!upstream.ok) return res.status(502).json({ error: 'Chat service rejected request' });
      const token = process.env.TELEGRAM_BOT_TOKEN;
      if (!token) return res.status(200).json({ ok: true, mock: true, reply: answer.reply });
      const sent = await fetchImpl(`https://api.telegram.org/bot${token}/sendMessage`, {
        method: 'POST', headers: { 'content-type': 'application/json' },
        body: JSON.stringify({ chat_id: message.chat.id, text: answer.reply })
      });
      if (!sent.ok) return res.status(502).json({ error: 'Telegram sendMessage failed' });
      return res.json({ ok: true });
    } catch {
      return res.status(502).json({ error: 'Chat service is unavailable' });
    }
  });
  return app;
}

if (process.env.NODE_ENV !== 'test') {
  createApp().listen(Number(process.env.PORT ?? 3000), () => console.log(`Gateway listening on ${process.env.PORT ?? 3000}`));
}

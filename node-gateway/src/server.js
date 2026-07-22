import './load-env.js';
import express from 'express';
import { askChatBot } from './chat-client.js';

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
      const body = await askChatBot({ sessionId, message, channel, consentToContact, fetchImpl });
      return res.json(body);
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
      const answer = await askChatBot({ sessionId: message.chat.id, message: message.text, fetchImpl });
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

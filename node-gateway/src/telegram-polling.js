import './load-env.js';
import { askChatBot } from './chat-client.js';

const token = process.env.TELEGRAM_BOT_TOKEN;
if (!token) throw new Error('TELEGRAM_BOT_TOKEN is not configured');

const telegramUrl = `https://api.telegram.org/bot${token}`;
let offset = 0;
let stopped = false;

async function telegram(method, payload = {}) {
  const response = await fetch(`${telegramUrl}/${method}`, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify(payload)
  });
  const body = await response.json();
  if (!response.ok || !body.ok) throw new Error(`Telegram ${method} failed: ${body.description ?? response.status}`);
  return body.result;
}

async function handleUpdate(update) {
  const message = update.message;
  if (!message?.chat?.id || typeof message.text !== 'string') return;
  try {
    await telegram('sendChatAction', { chat_id: message.chat.id, action: 'typing' });
    const answer = await askChatBot({ sessionId: message.chat.id, message: message.text });
    await telegram('sendMessage', { chat_id: message.chat.id, text: answer.reply });
  } catch (error) {
    console.error(`Update ${update.update_id} failed: ${error.message}`);
    await telegram('sendMessage', { chat_id: message.chat.id, text: 'Сервис временно недоступен. Пожалуйста, повторите запрос позднее.' }).catch(() => {});
  }
}

async function run() {
  const bot = await telegram('getMe');
  console.log(`Telegram bot @${bot.username} connected in polling mode`);
  await telegram('deleteWebhook', { drop_pending_updates: false });
  while (!stopped) {
    try {
      const updates = await telegram('getUpdates', { offset, timeout: 30, allowed_updates: ['message'] });
      for (const update of updates) {
        offset = update.update_id + 1;
        await handleUpdate(update);
      }
    } catch (error) {
      console.error(`Polling error: ${error.message}`);
      await new Promise(resolve => setTimeout(resolve, 3000));
    }
  }
}

process.once('SIGINT', () => { stopped = true; });
process.once('SIGTERM', () => { stopped = true; });
run().catch(error => {
  console.error(error.message);
  process.exitCode = 1;
});


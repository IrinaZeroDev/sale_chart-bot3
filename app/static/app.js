const API_PATH = '/api/v1/public/chat';
const SESSION_KEY = 'sales-assistant-session';
const messagesElement = document.querySelector('#messages');
const formElement = document.querySelector('#chat-form');
const inputElement = document.querySelector('#message-input');
const sendButtonElement = document.querySelector('#send-button');
const providerElement = document.querySelector('#provider-name');
const quickActionElements = document.querySelectorAll('[data-message]');

const getSessionId = () => {
  const existingId = sessionStorage.getItem(SESSION_KEY);
  if (existingId) return existingId;
  const newId = crypto.randomUUID();
  sessionStorage.setItem(SESSION_KEY, newId);
  return newId;
};

const appendMessage = (text, type) => {
  const messageElement = document.createElement('p');
  messageElement.className = `message ${type}`;
  messageElement.textContent = text;
  messagesElement.append(messageElement);
  messagesElement.scrollTop = messagesElement.scrollHeight;
};

const sendMessage = async message => {
  appendMessage(message, 'user');
  sendButtonElement.disabled = true;
  inputElement.disabled = true;
  try {
    const response = await fetch(API_PATH, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ session_id: getSessionId(), message, channel: 'web-mvp' })
    });
    const body = await response.json();
    if (!response.ok) throw new Error(body.detail ?? 'Сервис временно недоступен');
    appendMessage(body.reply, 'bot');
  } catch (error) {
    appendMessage(error.message, 'bot error');
  } finally {
    sendButtonElement.disabled = false;
    inputElement.disabled = false;
    inputElement.focus();
  }
};

const chatSubmitHandler = event => {
  event.preventDefault();
  const message = inputElement.value.trim();
  if (!message) return;
  inputElement.value = '';
  sendMessage(message);
};

formElement.addEventListener('submit', chatSubmitHandler);
quickActionElements.forEach(element => element.addEventListener('click', () => sendMessage(element.dataset.message)));

fetch('/health').then(response => response.json()).then(body => { providerElement.textContent = body.provider; }).catch(() => { providerElement.textContent = 'недоступен'; });
appendMessage('Здравствуйте. Чем могу помочь: информация о товарах, статус заказа или вопросы поддержки?', 'bot');

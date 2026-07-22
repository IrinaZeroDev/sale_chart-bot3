const API_PATH = '/api/v1/public/chat';
const SESSION_KEY = 'sales-assistant-session';
const MAX_TEXTAREA_HEIGHT = 112;

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

const scrollToLatest = () => {
  messagesElement.scrollTop = messagesElement.scrollHeight;
};

const removeWelcome = () => {
  messagesElement.querySelector('.welcome')?.remove();
};

const createMessageRow = (text, type) => {
  const rowElement = document.createElement('div');
  rowElement.className = `message-row ${type}`;
  const messageElement = document.createElement('p');
  messageElement.className = 'message';
  messageElement.textContent = text;
  if (type !== 'user') {
    const avatarElement = document.createElement('span');
    avatarElement.className = 'message-avatar';
    avatarElement.textContent = 'S';
    avatarElement.setAttribute('aria-hidden', 'true');
    rowElement.append(avatarElement);
  }
  rowElement.append(messageElement);
  return rowElement;
};

const appendMessage = (text, type) => {
  removeWelcome();
  messagesElement.append(createMessageRow(text, type));
  scrollToLatest();
};

const showTyping = () => {
  const rowElement = createMessageRow('', 'bot');
  rowElement.dataset.typing = 'true';
  const messageElement = rowElement.querySelector('.message');
  messageElement.classList.add('typing');
  for (let index = 0; index < 3; index += 1) messageElement.append(document.createElement('i'));
  messagesElement.append(rowElement);
  scrollToLatest();
};

const removeTyping = () => {
  messagesElement.querySelector('[data-typing]')?.remove();
};

const setPendingState = isPending => {
  sendButtonElement.disabled = isPending;
  inputElement.disabled = isPending;
  quickActionElements.forEach(element => { element.disabled = isPending; });
};

const resizeInput = () => {
  inputElement.style.height = 'auto';
  inputElement.style.height = `${Math.min(inputElement.scrollHeight, MAX_TEXTAREA_HEIGHT)}px`;
};

const sendMessage = async message => {
  appendMessage(message, 'user');
  setPendingState(true);
  showTyping();
  try {
    const response = await fetch(API_PATH, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ session_id: getSessionId(), message, channel: 'web-mvp' })
    });
    const body = await response.json();
    if (!response.ok) throw new Error(body.detail ?? 'Сервис временно недоступен');
    removeTyping();
    appendMessage(body.reply, 'bot');
  } catch (error) {
    removeTyping();
    appendMessage(error.message, 'error');
  } finally {
    setPendingState(false);
    inputElement.focus();
  }
};

const chatSubmitHandler = event => {
  event.preventDefault();
  const message = inputElement.value.trim();
  if (!message) return;
  inputElement.value = '';
  resizeInput();
  sendMessage(message);
};

const inputKeydownHandler = event => {
  if (event.key !== 'Enter' || event.shiftKey || event.isComposing) return;
  event.preventDefault();
  formElement.requestSubmit();
};

formElement.addEventListener('submit', chatSubmitHandler);
inputElement.addEventListener('input', resizeInput);
inputElement.addEventListener('keydown', inputKeydownHandler);
quickActionElements.forEach(element => element.addEventListener('click', () => sendMessage(element.dataset.message)));

fetch('/health')
  .then(response => response.json())
  .then(body => { providerElement.textContent = body.provider; })
  .catch(() => { providerElement.textContent = 'недоступен'; });

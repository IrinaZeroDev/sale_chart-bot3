export async function askChatBot({ sessionId, message, channel = 'telegram', consentToContact, fetchImpl = fetch }) {
  const response = await fetchImpl(`${process.env.PYTHON_API_URL ?? 'http://localhost:8000'}/api/v1/chat`, {
    method: 'POST',
    headers: {
      'content-type': 'application/json',
      'x-api-key': process.env.INTERNAL_API_KEY ?? 'change-me'
    },
    body: JSON.stringify({
      session_id: String(sessionId),
      message,
      channel,
      consent_to_contact: consentToContact
    })
  });
  const body = await response.json();
  if (!response.ok) throw new Error(`Chat API returned ${response.status}`);
  return body;
}


import api, { fetch } from '@forge/api';

interface AnalyzePayload {
  queryText?: string;
  screenshotId?: string;
  context?: Record<string, unknown>;
}

export async function handleAnalyze(req: { payload: AnalyzePayload }) {
  const payload = req.payload || {};
  const gatewayUrl = process.env.AI_GATEWAY_URL || 'http://localhost:8000';
  const endpoint = `${gatewayUrl}/analyze`;

  // TODO: If screenshotId present, fetch media via Forge Media API once wired
  // TODO: Optionally augment with Jira/Confluence context via REST API

  const response = await fetch(endpoint, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      query_text: payload.queryText,
      screenshot_id: payload.screenshotId,
      context: payload.context || {}
    })
  });

  if (!response.ok) {
    const text = await response.text();
    return {
      ok: false,
      error: `Gateway error: ${response.status} ${text}`
    };
  }

  const data = await response.json();
  return { ok: true, data };
}

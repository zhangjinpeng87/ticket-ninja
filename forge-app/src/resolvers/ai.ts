import api, { fetch, storage } from '@forge/api';

interface AnalyzePayload {
  queryText?: string;
  screenshotId?: string;
  context?: Record<string, unknown>;
}

export async function handleAnalyze(req: { payload: AnalyzePayload; context: any }) {
  const payload = req.payload || {};
  const issueContext = req.context || {};
  // Forge requires HTTPS - use localtunnel or ngrok for local development
  // Set AI_GATEWAY_URL environment variable: forge variables set AI_GATEWAY_URL https://your-tunnel-url.loca.lt
  const gatewayUrl = process.env.AI_GATEWAY_URL;
  if (!gatewayUrl) {
    return {
      ok: false,
      error: 'AI_GATEWAY_URL environment variable is not set. Please set it using: forge variables set AI_GATEWAY_URL https://your-tunnel-url.loca.lt'
    };
  }
  const endpoint = `${gatewayUrl}/analyze`;

  // TODO: If screenshotId present, fetch media via Forge Media API once wired
  
  // Build context with issue information
  const context = {
    ...(payload.context || {}),
    issue: issueContext.issueKey ? {
      key: issueContext.issueKey,
      type: issueContext.issueType,
      summary: issueContext.issueSummary,
      description: issueContext.issueDescription,
    } : {}
  };

  const response = await fetch(endpoint, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      query_text: payload.queryText,
      screenshot_id: payload.screenshotId,
      context
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

export async function getIssueContext(req: { payload: { issueKey?: string }; context: any }) {
  // Get issue key from context (automatically available in issue panels)
  const context = req.context || {};
  const issueKey = context.extension?.issue?.key;
  
  if (!issueKey) {
    return { ok: false, error: 'No issue key found in context' };
  }

  // For now, return basic info from context
  // TODO: Enhance to fetch full issue details via Jira API if needed
  // Note: Full API implementation would require proper Route type handling
  return {
    ok: true,
    data: {
      issueKey,
      // Additional fields can be fetched via API if needed
    }
  };
}

export async function getMessages(req: { payload: { issueKey: string } }) {
  const { issueKey } = req.payload;
  
  if (!issueKey) {
    return { ok: false, error: 'Issue key is required' };
  }

  try {
    const storageKey = `messages-${issueKey}`;
    const messages = await storage.get(storageKey);
    
    return {
      ok: true,
      data: messages || []
    };
  } catch (err: any) {
    return {
      ok: false,
      error: `Failed to load messages: ${err.message}`
    };
  }
}

export async function saveMessages(req: { payload: { issueKey: string; messages: any[] } }) {
  const { issueKey, messages } = req.payload;
  
  if (!issueKey) {
    return { ok: false, error: 'Issue key is required' };
  }

  try {
    const storageKey = `messages-${issueKey}`;
    await storage.set(storageKey, messages);
    
    return {
      ok: true,
      data: { success: true }
    };
  } catch (err: any) {
    return {
      ok: false,
      error: `Failed to save messages: ${err.message}`
    };
  }
}

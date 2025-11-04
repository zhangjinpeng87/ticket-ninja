import api, { fetch } from '@forge/api';

interface AnalyzePayload {
  queryText?: string;
  screenshotId?: string;
  context?: Record<string, unknown>;
}

export async function handleAnalyze(req: { payload: AnalyzePayload; context: any }) {
  const payload = req.payload || {};
  const issueContext = req.context || {};
  const gatewayUrl = process.env.AI_GATEWAY_URL || 'http://localhost:8000';
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

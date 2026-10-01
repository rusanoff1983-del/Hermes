import {
  ANTIGRAVITY_CLIENT_ID,
  ANTIGRAVITY_CLIENT_SECRET,
  ANTIGRAVITY_REDIRECT_URI,
  ANTIGRAVITY_SCOPES,
  buildAntigravityLoadCodeAssistMetadata,
  fetchWithAgyCliTransport,
  buildAntigravityHarnessUserAgent,
  buildAgyAgentRequestMetadata,
  createAgyRequestSessionContext,
  orderAgyRequestPayloadInPlace,
  applyGeminiTransforms
} from '@cortexkit/antigravity-auth-core';

const action = process.argv[2];

if (action === 'config') {
  process.stdout.write(JSON.stringify({
    clientId: ANTIGRAVITY_CLIENT_ID,
    clientSecret: ANTIGRAVITY_CLIENT_SECRET,
    redirectUri: ANTIGRAVITY_REDIRECT_URI,
    scopes: ANTIGRAVITY_SCOPES,
    metadata: buildAntigravityLoadCodeAssistMetadata()
  }));
} else if (action === 'request') {
  let input = '';
  for await (const x of process.stdin) {
    input += x;
    if (input.length > 16 * 1024 * 1024) throw new Error('Request too large');
  }
  const x = JSON.parse(input);
  const u = new URL(x.url);
  const allowed = ['daily-cloudcode-pa.googleapis.com', 'cloudcode-pa.googleapis.com'];
  if (u.protocol !== 'https:' || !allowed.includes(u.hostname) || u.port || !['/v1internal:loadCodeAssist', '/v1internal:fetchAvailableModels', '/v1internal:streamGenerateContent'].includes(u.pathname)) {
    throw new Error('Endpoint rejected');
  }
  let body = x.body;
  if (u.pathname.includes('streamGenerateContent')) {
    applyGeminiTransforms(body.request, { model: body.model });
    const ctx = createAgyRequestSessionContext('hermes-antigravity-direct');
    const meta = buildAgyAgentRequestMetadata(ctx, body.request, body.model);
    body.request.labels = meta.labels;
    body.request.sessionId = meta.sessionId;
    orderAgyRequestPayloadInPlace(body.request);
    body = {
      project: body.project,
      requestId: meta.requestId,
      request: body.request,
      model: body.model,
      userAgent: 'antigravity',
      requestType: 'agent'
    };
  }
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 150000);
  try {
    const res = await fetchWithAgyCliTransport(
      x.url,
      {
        method: 'POST',
        headers: {
          'User-Agent': buildAntigravityHarnessUserAgent(),
          'X-Hermes-Attribution': 'hermes-antigravity-direct/0.1.0',
          Authorization: 'Bearer ' + x.token,
          'Content-Type': 'application/json',
          'Accept-Encoding': 'gzip'
        },
        body: JSON.stringify(body)
      },
      { timeoutMs: 30000, idleTimeoutMs: 30000, signal: controller.signal }
    );
    let text = '', bytes = 0;
    const decoder = new TextDecoder('utf-8');
    if (res.body) {
      for await (const chunk of res.body) {
        bytes += chunk.byteLength;
        if (bytes > 8 * 1024 * 1024) throw new Error('Response too large');
        text += decoder.decode(chunk, { stream: true });
      }
    }
    text += decoder.decode();
    const events = [];
    if (res.ok) {
      if (text.trim().startsWith('{') || text.trim().startsWith('[')) {
        const v = JSON.parse(text);
        events.push(...(Array.isArray(v) ? v : [v]));
      } else {
        for (const frame of text.replaceAll('\r\n', '\n').split('\n\n')) {
          const data = frame.split('\n').filter(l => l.startsWith('data:')).map(l => l.slice(5).trimStart()).join('\n');
          if (data && data !== '[DONE]') {
            events.push(JSON.parse(data));
          }
        }
      }
    }
    process.stdout.write(JSON.stringify({ status: res.status, events }));
  } finally {
    clearTimeout(timer);
  }
} else {
  throw new Error('Unsupported wire action');
}

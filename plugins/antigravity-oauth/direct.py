"""Direct Hermes Antigravity route.
Protocol reference: suntianc/dsh-antigravity-auth (MIT), cortexkit auth core 2.2.0.
Gemini text and tool requests supported.
"""
import ctypes
from ctypes import wintypes
import hashlib
import hmac
import http.server
import json
import os
from pathlib import Path
import secrets
import subprocess
import threading
import time
import urllib.parse
import uuid
import webbrowser

ROOT = Path(__file__).parent
# Prevent console flashes when the GUI backend starts the wire helper.
_SUBPROCESS_FLAGS = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
CARRIER = 'antigravity-direct.native_assistant'
# Nonsecret routing marker. Real tokens exist only inside DPAPI storage.
LOCAL_MARKER = 'antigravity-direct-local'
ORIGIN = 'https://daily-cloudcode-pa.googleapis.com'
_LOCK = threading.RLock()

class Blob(ctypes.Structure):
    _fields_ = [('size', wintypes.DWORD), ('data', ctypes.POINTER(ctypes.c_ubyte))]

def _crypt(raw, decrypt=False):
    buf = ctypes.create_string_buffer(raw)
    source = Blob(len(raw), ctypes.cast(buf, ctypes.POINTER(ctypes.c_ubyte)))
    target = Blob()
    dll = ctypes.WinDLL('crypt32', use_last_error=True)
    fn = dll.CryptUnprotectData if decrypt else dll.CryptProtectData
    fn.argtypes = [ctypes.POINTER(Blob), ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(Blob)]
    fn.restype = wintypes.BOOL
    if not fn(ctypes.byref(source), None, None, None, None, 1, ctypes.byref(target)):
        raise RuntimeError('Windows DPAPI failed')
    try:
        return ctypes.string_at(target.data, target.size)
    finally:
        kernel = ctypes.WinDLL('kernel32')
        kernel.LocalFree.argtypes = [ctypes.c_void_p]
        kernel.LocalFree.restype = ctypes.c_void_p
        kernel.LocalFree(target.data)

def protect(raw):
    return _crypt(raw)

def unprotect(raw):
    return _crypt(raw, True)

def store_path():
    home = Path(os.environ.get('HERMES_HOME', str(Path.home() / 'AppData/Local/hermes')))
    return home / 'plugin-data/antigravity-direct/credential.dpapi'

def save(record):
    path = store_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    data = protect(json.dumps(record).encode())
    tmp = path.with_name('credential.' + uuid.uuid4().hex + '.tmp')
    try:
        tmp.write_bytes(data)
        os.replace(tmp, path)
    finally:
        tmp.unlink(missing_ok=True)

def load():
    p = store_path()
    if not p.exists():
        raise RuntimeError('Antigravity Direct: login required')
    return json.loads(unprotect(p.read_bytes()))

def public_config():
    run = subprocess.run(['node', str(ROOT / 'wire.mjs'), 'config'], capture_output=True, text=True, encoding='utf-8', creationflags=_SUBPROCESS_FLAGS, timeout=15)
    if run.returncode:
        raise RuntimeError('Antigravity wire library unavailable')
    return json.loads(run.stdout)

def post_json(url, token, body):
    req = {'url': url, 'token': token, 'body': body}
    run = subprocess.run(['node', str(ROOT / 'wire.mjs'), 'request'], input=json.dumps(req), capture_output=True, text=True, encoding='utf-8', creationflags=_SUBPROCESS_FLAGS, timeout=180)
    if run.returncode:
        raise RuntimeError('Antigravity transport failed (details suppressed)')
    response = json.loads(run.stdout)
    if response['status'] >= 400:
        raise RuntimeError('Antigravity HTTP ' + str(response['status']))
    return response['events']

MAINTAINED_MODELS = (
    'gemini-3.8-flash-high', 'gemini-3.8-flash-medium', 'gemini-3.8-flash-low',
    'gemini-3.7-flash-high', 'gemini-3.7-flash-medium', 'gemini-3.7-flash-low',
    'gemini-3.6-flash-high', 'gemini-3.6-flash-medium', 'gemini-3.6-flash-low',
    'gemini-3.5-flash-high', 'gemini-3.5-flash-medium', 'gemini-3.5-flash-low',
    'gemini-3.1-pro-high', 'gemini-3.1-pro-low',
    'claude-sonnet-4-6', 'claude-opus-4-6-thinking', 'gpt-oss-120b-medium',
)

def fetch_models():
    x = credential()
    events = post_json(ORIGIN + '/v1internal:fetchAvailableModels', x['accessToken'], {'project': x['projectId']})
    payload = events[0] if events else None
    live = payload.get('models') if isinstance(payload, dict) else None
    if not isinstance(live, dict):
        raise RuntimeError('Unexpected fetchAvailableModels response')
    return [m for m in MAINTAINED_MODELS if m in live]

def token_post(config, data):
    import httpx
    response = httpx.post('https://oauth2.googleapis.com/token', data={**data, 'client_id': config['clientId'], 'client_secret': config['clientSecret']}, timeout=20, follow_redirects=False)
    if response.status_code != 200:
        raise RuntimeError('Google token exchange HTTP ' + str(response.status_code))
    x = response.json()
    if not x.get('access_token'):
        raise RuntimeError('No access token in Google response')
    return x

def credential():
    with _LOCK:
        x = load()
        if x['expiresAt'] <= time.time() + 300:
            t = token_post(public_config(), {'grant_type': 'refresh_token', 'refresh_token': x['refreshToken']})
            x.update(accessToken=t['access_token'], refreshToken=t.get('refresh_token') or x['refreshToken'], expiresAt=time.time() + int(t['expires_in']))
            save(x)
        return x

def valid_callback(path, state):
    u = urllib.parse.urlsplit(path)
    q = urllib.parse.parse_qs(u.query)
    return u.path == '/oauth-callback' and len(q.get('state', [])) == 1 and hmac.compare_digest(q['state'][0], state) and (len(q.get('code', [])) == 1 or len(q.get('error', [])) == 1)

def login(timeout=300):
    cfg = public_config()
    verifier = secrets.token_urlsafe(32)
    state = secrets.token_urlsafe(32)
    challenge = __import__('base64').urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b'=').decode()
    deadline = time.monotonic() + timeout
    result = {'handled': False}

    class Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self, *args): pass
        def answer(self, status, message):
            self.send_response(status)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Cache-Control', 'no-store')
            self.send_header('Content-Security-Policy', "default-src 'none'; frame-ancestors 'none'")
            self.end_headers()
            self.wfile.write(('<h2>' + message + '</h2>').encode())
        def do_GET(self):
            if self.headers.get('Host') not in ('localhost:51121', '127.0.0.1:51121') or not valid_callback(self.path, state):
                self.answer(400, 'Invalid callback; login remains pending.')
                return
            if result['handled'] or time.monotonic() >= deadline:
                self.answer(409, 'Login expired or already processed.')
                return
            result['handled'] = True
            q = urllib.parse.parse_qs(urllib.parse.urlsplit(self.path).query)
            try:
                if 'error' in q:
                    raise RuntimeError('Google login declined')
                t = token_post(cfg, {'grant_type': 'authorization_code', 'code': q['code'][0], 'redirect_uri': cfg['redirectUri'], 'code_verifier': verifier})
                if not t.get('refresh_token'):
                    raise RuntimeError('No refresh token; login not saved')
                events = post_json(ORIGIN + '/v1internal:loadCodeAssist', t['access_token'], {'metadata': cfg['metadata']})
                p = events[0].get('cloudaicompanionProject')
                if isinstance(p, dict):
                    p = p.get('id')
                if not isinstance(p, str) or not p.strip():
                    raise RuntimeError('No project for account; no automatic onboarding performed')
                if time.monotonic() >= deadline:
                    raise RuntimeError('Login expired')
                save({'accessToken': t['access_token'], 'refreshToken': t['refresh_token'], 'expiresAt': time.time() + int(t['expires_in']), 'projectId': p})
                self.answer(200, 'Antigravity Direct connected. You can return to Hermes.')
                result['success'] = True
            except Exception as exc:
                result['error'] = str(exc)
                self.answer(400, 'Login could not complete. Return to Hermes for status.')

    server = http.server.HTTPServer(('127.0.0.1', 51121), Handler)
    server.timeout = 0.5
    params = {
        'client_id': cfg['clientId'],
        'response_type': 'code',
        'redirect_uri': cfg['redirectUri'],
        'scope': ' '.join(cfg['scopes']),
        'state': state,
        'code_challenge': challenge,
        'code_challenge_method': 'S256',
        'access_type': 'offline',
        'prompt': 'consent'
    }
    try:
        if not webbrowser.open('https://accounts.google.com/o/oauth2/v2/auth?' + urllib.parse.urlencode(params)):
            raise RuntimeError('Could not open browser')
        print('Waiting for Google login; no tokens are displayed.', flush=True)
        while not result['handled'] and time.monotonic() < deadline:
            server.handle_request()
        if not result.get('success'):
            raise RuntimeError(result.get('error', 'Login timeout'))
    finally:
        server.server_close()
    print('Connected; credential persisted with Windows DPAPI.')

def build_request(model, messages, project, tools=None, **kwargs):
    if 'image' in model:
        raise ValueError('Image models are not supported on the direct route')
    contents = []; systems = []; names = {}
    for m in messages:
        role = m['role']; text = m.get('content'); parts = []
        if role in ('system', 'developer'):
            if not isinstance(text, str):
                raise ValueError('Only text system prompts supported')
            systems.append({'text': text})
            continue
        if role == 'assistant':
            native = next((d.get('parts') for d in m.get('reasoning_details', []) or [] if isinstance(d, dict) and d.get('type') == CARRIER), None)
            for call in m.get('tool_calls', []) or []:
                names[call['id']] = call['function']['name']
            if native is not None:
                parts = native
            else:
                if text:
                    parts.append({'text': text})
                for call in m.get('tool_calls', []) or []:
                    parts.append({'functionCall': {'name': call['function']['name'], 'args': json.loads(call['function']['arguments'])}})
        elif role == 'tool':
            name = names.get(m.get('tool_call_id'))
            if not name:
                raise ValueError('Unmatched tool response')
            parts = [{'functionResponse': {'name': name, 'response': {'result': text}}}]
        elif role == 'user':
            if not isinstance(text, str):
                raise ValueError('Multimodal not implemented in verification slice')
            parts = [{'text': text}]
        else:
            raise ValueError('Unsupported message role')
        if parts:
            contents.append({'role': 'model' if role == 'assistant' else 'user', 'parts': parts})
    req = {'contents': contents, 'generationConfig': {'maxOutputTokens': kwargs.get('max_tokens', 8192)}}
    if systems:
        req['systemInstruction'] = {'role': 'user', 'parts': systems}
    if tools:
        req['tools'] = [{'functionDeclarations': [{'name': t['function']['name'], 'description': t['function'].get('description', ''), 'parameters': t['function'].get('parameters', {})} for t in tools]}]
    return {'model': model, 'project': project, 'request': req}

def parse_events(events, model):
    parts = []; usage = {}; finish = 'stop'
    for e in events:
        e = e.get('response', e)
        if e.get('error'):
            raise RuntimeError('Antigravity response error')
        if e.get('usageMetadata'):
            usage = e['usageMetadata']
        for c in e.get('candidates', []):
            parts.extend(c.get('content', {}).get('parts', []))
            if c.get('finishReason') == 'MAX_TOKENS':
                finish = 'length'
    calls = []
    for p in parts:
        if 'functionCall' in p:
            f = p['functionCall']
            calls.append({'id': 'call_' + uuid.uuid4().hex[:12], 'type': 'function', 'function': {'name': f['name'], 'arguments': json.dumps(f.get('args', {}))}})
    if calls:
        finish = 'tool_calls'
    message = {'role': 'assistant', 'content': ''.join(p.get('text', '') for p in parts if not p.get('thought')), 'reasoning_details': [{'type': CARRIER, 'parts': parts}]}
    if calls:
        message['tool_calls'] = calls
    inp = usage.get('promptTokenCount', 0); out = usage.get('candidatesTokenCount', 0)
    return {
        'id': 'chatcmpl-' + uuid.uuid4().hex,
        'object': 'chat.completion',
        'created': int(time.time()),
        'model': model,
        'choices': [{'index': 0, 'message': message, 'finish_reason': finish}],
        'usage': {'prompt_tokens': inp, 'completion_tokens': out, 'total_tokens': usage.get('totalTokenCount', inp + out)}
    }

class DirectClient:
    def __init__(self, **kwargs):
        from types import SimpleNamespace
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self.create))
        self.api_key = LOCAL_MARKER
        self.base_url = ORIGIN

    def create(self, model, messages, stream=False, tools=None, **kwargs):
        from openai.types.chat import ChatCompletion, ChatCompletionChunk
        x = credential()
        body = build_request(model, messages, x['projectId'], tools, **kwargs)
        events = post_json(ORIGIN + '/v1internal:streamGenerateContent?alt=sse', x['accessToken'], body)
        parsed = parse_events(events, model)
        if not stream:
            return ChatCompletion.model_validate(parsed)
        msg = parsed['choices'][0]['message']
        delta = dict(msg)
        if delta.get('tool_calls'):
            delta['tool_calls'] = [dict(c, index=i) for i, c in enumerate(delta['tool_calls'])]
        chunk = {k: parsed[k] for k in ('id', 'created', 'model')}
        chunk.update(object='chat.completion.chunk', choices=[{'index': 0, 'delta': delta, 'finish_reason': None}])
        end = {**chunk, 'choices': [{'index': 0, 'delta': {}, 'finish_reason': parsed['choices'][0]['finish_reason']}], 'usage': parsed['usage']}
        return iter([ChatCompletionChunk.model_validate(chunk), ChatCompletionChunk.model_validate(end)])

if __name__ == '__main__':
    import sys
    action = sys.argv[1] if len(sys.argv) > 1 else 'status'
    if action == 'login':
        login()
    elif action == 'status':
        cfg = public_config()
        print('OAuth configuration: available; node wire library: available')
        print('Credential:', 'present (encrypted)' if store_path().exists() else 'not signed in')
    elif action == 'probe':
        r = DirectClient().create(model='gemini-3.8-flash-low', messages=[{'role': 'user', 'content': 'Reply exactly OK.'}])
        print(r.choices[0].message.content)
    else:
        raise SystemExit('Expected login, status or probe')

"""Experimental Hermes direct Antigravity route. No agy, no token migration.
Protocol reference: suntianc/dsh-antigravity-auth (MIT), cortexkit auth core 2.2.0.
Only Gemini text/tool requests supported in this first verification slice.
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
import urllib.request
import urllib.error
import uuid
import webbrowser
import contextlib
import re
import unicodedata

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
    try: return ctypes.string_at(target.data, target.size)
    finally:
        kernel = ctypes.WinDLL('kernel32')
        kernel.LocalFree.argtypes = [ctypes.c_void_p]
        kernel.LocalFree.restype = ctypes.c_void_p
        kernel.LocalFree(target.data)

def protect(raw): return _crypt(raw)
def unprotect(raw): return _crypt(raw, True)

def store_path():
    home = Path(os.environ.get('HERMES_HOME', str(Path.home() / 'AppData/Local/hermes')))
    return home / 'plugin-data/antigravity-direct/credential.dpapi'

def accounts_path():
    return store_path().with_name('accounts.dpapi')

@contextlib.contextmanager
def store_lock(timeout=30):
    """OS byte-range lock, released even if a process dies. No stale lock deletion."""
    import msvcrt
    with _LOCK:
        path = accounts_path().with_suffix('.lock')
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('a+b') as f:
            if f.seek(0, 2) == 0:
                f.write(b'0'); f.flush()
            deadline = time.monotonic() + timeout
            while True:
                try:
                    f.seek(0); msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
                    break
                except OSError:
                    if time.monotonic() >= deadline: raise RuntimeError('Account store busy')
                    time.sleep(0.05)
            try: yield
            finally:
                f.seek(0); msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)

def _write_store(data):
    path = accounts_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name('accounts.' + uuid.uuid4().hex + '.tmp')
    try:
        tmp.write_bytes(protect(json.dumps(data).encode()))
        os.replace(tmp, path)
    finally: tmp.unlink(missing_ok=True)

def _read_store():
    path = accounts_path()
    if path.exists():
        data = json.loads(unprotect(path.read_bytes()))
        if data.get('version') != 1 or not isinstance(data.get('accounts'), dict):
            raise RuntimeError('Unsupported account store')
        return data
    legacy = store_path()
    if legacy.exists():
        record = json.loads(unprotect(legacy.read_bytes()))
        data = {'version': 1, 'accounts': {'primary': {'label': 'Основной', 'credential': record}}}
        _write_store(data)  # Legacy encrypted file remains untouched for rollback.
        return data
    return {'version': 1, 'accounts': {}}

def validate_account_id(account_id):
    if not isinstance(account_id, str) or not re.fullmatch(r'primary|a[0-9a-f]{32}', account_id):
        raise ValueError('Invalid account routing ID')
    return account_id

def validate_label(label):
    if not isinstance(label, str) or not label.strip() or len(label) > 64 or any(unicodedata.category(c).startswith('C') for c in label):
        raise ValueError('Account label must be 1-64 visible characters')
    return label.strip()

def accounts():
    with store_lock():
        return {i: {'label': a['label']} for i, a in _read_store()['accounts'].items()}

def load(account_id='primary'):
    validate_account_id(account_id)
    with store_lock():
        account = _read_store()['accounts'].get(account_id)
        if not account: raise RuntimeError('Antigravity Direct: unknown account or login required')
        return dict(account['credential'])

def save(record, account_id='primary'):
    validate_account_id(account_id)
    with store_lock():
        data = _read_store()
        if account_id not in data['accounts']:
            if account_id != 'primary': raise RuntimeError('Unknown account')
            data['accounts'][account_id] = {'label': 'Основной'}
        data['accounts'][account_id]['credential'] = dict(record)
        _write_store(data)

def identity(token):
    import httpx
    r = httpx.get('https://www.googleapis.com/oauth2/v3/userinfo', headers={'Authorization': 'Bearer '+token}, timeout=20, follow_redirects=False)
    if r.status_code != 200: raise RuntimeError('Google identity lookup failed')
    sub = r.json().get('sub')
    if not isinstance(sub, str) or not sub: raise RuntimeError('Google identity missing')
    return sub

def add_account(record, label, subject, primary_subject=None):
    label = validate_label(label)
    if not isinstance(subject, str) or not subject:
        raise ValueError('Google account identity required')
    with store_lock():
        data = _read_store(); rows = data['accounts']
        # Populate migrated primary identity only from its own existing token.
        if 'primary' in rows and not rows['primary'].get('subject'):
            if not primary_subject: raise RuntimeError('Cannot verify legacy primary identity; existing account unchanged')
            rows['primary']['subject'] = primary_subject
        match = next((i for i,a in rows.items() if a.get('subject') == subject), None)
        target = next((i for i,a in rows.items() if a['label'].casefold() == label.casefold()), None)
        if match is not None and target != match:
            raise RuntimeError('This Google account already exists under another label; use rename')
        if target is not None and match != target:
            raise RuntimeError('Label belongs to another Google account; use a different label')
        account_id = match or ('primary' if not rows else 'a'+uuid.uuid4().hex)
        rows[account_id] = {'label': label, 'subject': subject, 'credential': dict(record)}
        _write_store(data)
        return account_id

def rename_account(account_id, label):
    validate_account_id(account_id); label = validate_label(label)
    with store_lock():
        data = _read_store(); rows = data['accounts']
        if account_id not in rows: raise RuntimeError('Unknown account')
        if any(i != account_id and a['label'].casefold() == label.casefold() for i,a in rows.items()):
            raise ValueError('Duplicate account label')
        rows[account_id]['label'] = label
        _write_store(data)

def remove_account(account_id):
    validate_account_id(account_id)
    with store_lock():
        data = _read_store()
        if account_id not in data['accounts']: raise RuntimeError('Unknown account')
        del data['accounts'][account_id]
        _write_store(data)  # Empty store prevents resurrecting legacy credentials.
        if account_id == 'primary': store_path().unlink(missing_ok=True)

def route_model(model, account_id='primary'):
    validate_account_id(account_id)
    if not isinstance(model, str): raise ValueError('Invalid model')
    if '@' in model:
        match = re.fullmatch(r'([a-z0-9.-]+)@ag:(primary|a[0-9a-f]{32})', model)
        if not match: raise ValueError('Malformed account model tag')
        model, tagged = match.groups()
        if tagged != account_id: raise ValueError('Model account differs from selected provider')
    if model not in MAINTAINED_MODELS: raise ValueError('Unsupported model')
    if account_id not in accounts(): raise RuntimeError('Unknown account')
    return model

def _node_env():
    # Node's built-in fetch ignores HTTPS_PROXY unless NODE_USE_ENV_PROXY=1. Without a proxy the
    # Google endpoint answers 400 "User location is not supported for the API use" from RU
    # addresses, which surfaces to the user as the provider dying and the chain falling over.
    env = dict(os.environ)
    env['NODE_USE_ENV_PROXY'] = '1'
    # Отдельный прокси для Antigravity: домашний канал режет TLS к daily-cloudcode
    # (bad record MAC), поэтому ходим через CONNECT-прокси на WireGuard-адресе VPS.
    proxy = env.get('ANTIGRAVITY_PROXY')
    if not proxy:
        # The plugin can run inside a process that never exported the proxy vars; fall back to the
        # Hermes .env so a desktop restart is not required just to pick the proxy up.
        for candidate in (Path(os.environ.get('LOCALAPPDATA') or '') / 'hermes' / '.env',
                          Path.home() / '.hermes' / '.env'):
            try:
                for line in candidate.read_text(encoding='utf-8', errors='ignore').splitlines():
                    if line.strip().startswith(('ANTIGRAVITY_PROXY=', 'HTTPS_PROXY=', 'https_proxy=')):
                        proxy = line.split('=', 1)[1].strip()
                        break
            except OSError:
                pass
            if proxy:
                break
    if proxy:
        env.setdefault('HTTPS_PROXY', proxy)
        env.setdefault('HTTP_PROXY', proxy)
        env.setdefault('NO_PROXY', 'localhost,127.0.0.1')
    return env

def public_config():
    # Public desktop application configuration supplied by the same npm package as DSH.
    # Never inspect credentials belonging to agy or other apps.
    run = subprocess.run(['node', str(ROOT / 'wire.mjs'), 'config'], capture_output=True, text=True, encoding='utf-8', creationflags=_SUBPROCESS_FLAGS, timeout=15, env=_node_env())
    if run.returncode: raise RuntimeError('Antigravity wire library unavailable')
    return json.loads(run.stdout)



def _dbg(msg):
    try:
        import time as _t
        with open(Path(os.environ.get('LOCALAPPDATA') or '.') / 'hermes' / 'cache' / 'scratch' / 'agy_debug.log', 'a', encoding='utf-8') as f:
            f.write('%s pid=%s %s\n' % (_t.strftime('%H:%M:%S'), os.getpid(), msg))
    except Exception:
        pass

def _agy_proxy():
    """Прокси только для Antigravity: ANTIGRAVITY_PROXY из окружения или Hermes .env."""
    p = os.environ.get('ANTIGRAVITY_PROXY')
    if not p:
        for candidate in (Path(os.environ.get('LOCALAPPDATA') or '') / 'hermes' / '.env',
                          Path.home() / '.hermes' / '.env'):
            try:
                for line in candidate.read_text(encoding='utf-8', errors='ignore').splitlines():
                    if line.strip().startswith('ANTIGRAVITY_PROXY='):
                        p = line.split('=', 1)[1].strip()
                        break
            except OSError:
                pass
            if p:
                break
    return p or None

_AGY_UA = 'antigravity/cli/1.1.24 (aidev_client; os_type=windows; arch=amd64; cl=974782877; auth_method=consumer)'

def _proxy_post(url, token, body, proxy):
    """Прямой запрос через CONNECT-прокси VPS. Возвращает список событий."""
    data = json.dumps(body).encode()
    headers = {'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json', 'User-Agent': _AGY_UA}
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({'http': proxy, 'https': proxy}))
    _dbg('proxy request -> %s via %s' % (url.split('/')[-1], proxy))
    req = urllib.request.Request(url, data=data, method='POST', headers=headers)
    try:
        with opener.open(req, timeout=300) as r:
            raw = r.read().decode('utf-8', 'replace')
    except urllib.error.HTTPError as e:
        text = e.read().decode('utf-8', 'replace')[:400]
        raise RuntimeError('Antigravity HTTP %s: %s' % (e.code, text)) from None
    except Exception as e:
        raise RuntimeError('Antigravity transport failed [class=%s code=TRANSPORT_ERROR phase=connect]' % type(e).__name__) from None
    raw = raw.strip()
    if raw.startswith('data:'):
        events = []
        for line in raw.splitlines():
            line = line.strip()
            if line.startswith('data:'):
                chunk = line[5:].strip()
                if chunk and chunk != '[DONE]':
                    try:
                        events.append(json.loads(chunk))
                    except ValueError:
                        pass
        return events
    parsed = json.loads(raw)
    return parsed if isinstance(parsed, list) else [parsed]

def _tokfp(t):
    import hashlib
    return hashlib.sha256((t or '').encode()).hexdigest()[:8]


def post_json(url, token, body):
    _px = _agy_proxy()
    _dbg('post_json start proxy=%s url=%s body=%d tok=%s' % (_px, url.split('/')[-1], len(json.dumps(body)), _tokfp(token)))
    try:
        import pathlib as _pl
        _pl.Path(os.environ.get('LOCALAPPDATA') or '.').joinpath('hermes','cache','scratch','last_payload.json').write_text(json.dumps(body, ensure_ascii=False), encoding='utf-8')
    except Exception:
        pass
    if _px:
        _t0 = time.time()
        try:
            _r = _proxy_post(url, token, body, _px)
            _dbg('post_json ok %.1fs events=%d' % (time.time() - _t0, len(_r)))
            return _r
        except Exception as _e:
            _dbg('post_json fail %.1fs %s: %s' % (time.time() - _t0, type(_e).__name__, str(_e)[:160]))
            raise

    # Reuse audited raw framing from DSH's library rather than invent a fingerprint.
    req = {'url':url, 'token':token, 'body':body}
    try:
        run = subprocess.run(['node', str(ROOT / 'wire.mjs'), 'request'], input=json.dumps(req), capture_output=True, text=True, encoding='utf-8', creationflags=_SUBPROCESS_FLAGS, timeout=330, env=_node_env())
    except subprocess.TimeoutExpired:
        raise RuntimeError('Antigravity transport failed [class=TimeoutExpired code=PROCESS_TIMEOUT phase=helper]') from None
    try:
        response = json.loads(run.stdout)
        if not isinstance(response, dict):
            raise ValueError('Invalid helper envelope')
    except (ValueError, TypeError):
        raise RuntimeError('Antigravity transport failed [class=Error code=HELPER_PROTOCOL phase=helper]') from None
    if run.returncode:
        d = response.get('transportError', {})
        if not isinstance(d, dict): d = {}
        # Defense in depth: do not trust arbitrary helper values or stderr.
        classes = {'Error', 'TypeError', 'SyntaxError', 'AbortError'}
        codes = {'TOTAL_TIMEOUT','IDLE_TIMEOUT','HEADER_TIMEOUT','CONNECT_TIMEOUT','INVALID_RESPONSE','RESPONSE_LIMIT','ECONNRESET','ECONNREFUSED','ETIMEDOUT','EPIPE','ENOTFOUND','EAI_AGAIN','ERR_STREAM_PREMATURE_CLOSE','Z_DATA_ERROR','TRANSPORT_ERROR'}
        cls = d.get('class') if isinstance(d.get('class'),str) and d.get('class') in classes else 'Error'
        code = d.get('code') if isinstance(d.get('code'),str) and d.get('code') in codes else 'TRANSPORT_ERROR'
        phase = d.get('phase') if isinstance(d.get('phase'),str) and d.get('phase') in {'connect','headers','body','parse'} else 'helper'
        elapsed = d.get('elapsedMs') if type(d.get('elapsedMs')) is int else 0
        raise RuntimeError(f'Antigravity transport failed [class={cls} code={code} phase={phase} elapsedMs={elapsed}]')
    if response['status'] >= 400:
        # Preserve Google's own error body (rate-limit reason, quota kind) instead of
        # reducing it to a bare status code; also append it to a local debug log so a
        # burst of 429s can be post-mortemed without re-sending traffic.
        msg = response.get('errorMessage') or response.get('rawError') or ''
        if not isinstance(msg, str): msg = json.dumps(msg, ensure_ascii=False)[:800] if msg else ''
        try:
            with open(ROOT / 'http-errors.log', 'a', encoding='utf-8') as f:
                f.write(time.strftime('%Y-%m-%d %H:%M:%S') + f' HTTP {response["status"]} {msg[:800]}\n')
        except OSError: pass
        raise RuntimeError('Antigravity HTTP ' + str(response['status']) + (': ' + msg[:400] if msg else ''))
    return response['events']

# Reviewed account-visible catalog (same descriptors DSH maintains for this route).
# fetch_models() reconciles it with the account's official model list, so the picker
# shows every model the signed-in login can actually use.
MAINTAINED_MODELS = (
    'gemini-3.8-flash-high', 'gemini-3.8-flash-medium', 'gemini-3.8-flash-low',
    'gemini-3.7-flash-high', 'gemini-3.7-flash-medium', 'gemini-3.7-flash-low',
    'gemini-3.6-flash-high', 'gemini-3.6-flash-medium', 'gemini-3.6-flash-low',
    'gemini-3.5-flash-high', 'gemini-3.5-flash-medium', 'gemini-3.5-flash-low',
    'gemini-3.1-pro-high', 'gemini-3.1-pro-low',
    'claude-sonnet-4-6', 'claude-opus-4-6-thinking', 'gpt-oss-120b-medium',
)

def fetch_models(account_id='primary'):
    """Live discovery scoped strictly to one account."""
    x = credential(account_id)
    events = post_json(ORIGIN + '/v1internal:fetchAvailableModels', x['accessToken'], {'project': x['projectId']})
    payload = events[0] if events else None
    live = payload.get('models') if isinstance(payload, dict) else None
    if not isinstance(live, dict): raise RuntimeError('Unexpected fetchAvailableModels response')
    return [m for m in MAINTAINED_MODELS if m in live]

def token_post(config, data):
    import httpx
    response = httpx.post('https://oauth2.googleapis.com/token', data={**data,'client_id':config['clientId'],'client_secret':config['clientSecret']}, timeout=20, follow_redirects=False)
    if response.status_code != 200: raise RuntimeError('Google token exchange HTTP ' + str(response.status_code))
    x = response.json()
    if not x.get('access_token'): raise RuntimeError('No access token in Google response')
    return x

_IDE_CACHE = {'at': None, 'exp': 0}

def _detect_ide_client():
    """Ищет OAuth-данные desktop-клиента Antigravity в установленном приложении.
    Они лежат в бинарнике открытым текстом, поэтому в репозиторий их класть нельзя
    (GitHub push protection блокирует такие строки)."""
    import re as _re, glob as _glob
    cands = []
    for pat in (
        os.path.join(os.environ.get('LOCALAPPDATA') or '', 'agy', 'bin', 'agy.exe'),
        os.path.join(os.environ.get('LOCALAPPDATA') or '', 'Programs', 'Antigravity', 'Antigravity.exe'),
    ):
        cands.append(pat)
    for base in (os.path.join(os.environ.get('LOCALAPPDATA') or '', 'Programs', 'Antigravity'),
                 os.path.join(os.environ.get('LOCALAPPDATA') or '', 'Programs', 'Antigravity IDE')):
        cands += _glob.glob(os.path.join(base, '**', '*.exe'), recursive=True)[:8]
    ids, secrets = set(), set()
    for path in cands:
        try:
            if not os.path.exists(path) or os.path.getsize(path) < 1000000:
                continue
            with open(path, 'rb') as f:
                data = f.read()
            ids.update(m.decode() for m in _re.findall(rb'[0-9]{10,}-[a-z0-9]{20,}\.apps\.googleusercontent\.com', data))
            secrets.update(m.decode() for m in _re.findall(rb'GOCSPX-[A-Za-z0-9_-]{28}', data))
        except Exception:
            continue
    return sorted(ids), sorted(secrets)



def _ide_credential():
    """Токен живого приложения Antigravity из хранилища Windows (gemini:antigravity).
    Обновляется тем же client_id/secret, что и само приложение, поэтому живёт бессрочно."""
    ctypes = __import__('ctypes'); wintypes = __import__('ctypes.wintypes', fromlist=['x'])
    class _C(ctypes.Structure):
        _fields_ = [('Flags', wintypes.DWORD), ('Type', wintypes.DWORD), ('TargetName', wintypes.LPWSTR),
                    ('Comment', wintypes.LPWSTR), ('LastWritten', wintypes.FILETIME),
                    ('CredentialBlobSize', wintypes.DWORD), ('CredentialBlob', ctypes.POINTER(ctypes.c_byte)),
                    ('Persist', wintypes.DWORD), ('AttributeCount', wintypes.DWORD),
                    ('Attributes', ctypes.c_void_p), ('TargetAlias', wintypes.LPWSTR), ('UserName', wintypes.LPWSTR)]
    adv = ctypes.windll.advapi32
    pc = ctypes.POINTER(_C)()
    if not adv.CredReadW(ctypes.c_wchar_p('gemini:antigravity'), 1, 0, ctypes.byref(pc)):
        raise RuntimeError('Antigravity Direct: приложение Antigravity не авторизовано')
    try:
        raw = ctypes.string_at(pc.contents.CredentialBlob, pc.contents.CredentialBlobSize)
    finally:
        adv.CredFree(pc)
    d = json.loads(raw.decode('utf-8'))
    t = d.get('token') or {}
    at, rt = t.get('access_token'), t.get('refresh_token')
    if _IDE_CACHE['at'] and _IDE_CACHE['exp'] > time.time() + 120:
        return {'accessToken': _IDE_CACHE['at'], 'refreshToken': rt, 'expiresAt': _IDE_CACHE['exp']}
    if not at or t.get('expiry'):
        pass
    px = _agy_proxy()
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({'http': px, 'https': px})) if px else urllib.request.build_opener()
    ids, secrets = ([IDE_CLIENT_ID], [IDE_CLIENT_SECRET]) if (IDE_CLIENT_ID and IDE_CLIENT_SECRET) else _detect_ide_client()
    j = None
    last_err = None
    for cid in ids:
        for sec in secrets:
            body = urllib.parse.urlencode({'client_id': cid, 'client_secret': sec,
                                           'grant_type': 'refresh_token', 'refresh_token': rt}).encode()
            try:
                with opener.open(urllib.request.Request('https://oauth2.googleapis.com/token', data=body), timeout=20) as resp:
                    j = json.loads(resp.read().decode('utf-8'))
                break
            except Exception as e:
                last_err = e
        if j:
            break
    if not j:
        raise last_err or RuntimeError('Antigravity Direct: не найдены OAuth-данные Antigravity IDE (задай ANTIGRAVITY_IDE_CLIENT_ID/SECRET)')
    _IDE_CACHE.update(at=j['access_token'], exp=time.time() + int(j.get('expires_in') or 3599))
    return {'accessToken': j['access_token'], 'refreshToken': j.get('refresh_token') or rt, 'expiresAt': _IDE_CACHE['exp']}

IDE_CLIENT_ID = os.environ.get('ANTIGRAVITY_IDE_CLIENT_ID', '')
IDE_CLIENT_SECRET = os.environ.get('ANTIGRAVITY_IDE_CLIENT_SECRET', '')


def credential(account_id='primary'):
    validate_account_id(account_id)
    with store_lock(timeout=60):
        data = _read_store()
        account = data['accounts'].get(account_id)
        if not account: raise RuntimeError('Antigravity Direct: unknown account or login required')
        x = dict(account['credential'])
        try:
            xi = _ide_credential()
            _dbg('cred source=ide tok=%s' % _tokfp(xi['accessToken']))
            x.update(accessToken=xi['accessToken'], refreshToken=xi['refreshToken'], expiresAt=xi['expiresAt'])
        except Exception:
            pass
        if x['expiresAt'] <= time.time() + 300:
            t = token_post(public_config(), {'grant_type':'refresh_token','refresh_token':x['refreshToken']})
            x.update(accessToken=t['access_token'], refreshToken=t.get('refresh_token') or x['refreshToken'], expiresAt=time.time()+int(t['expires_in']))
            account['credential'] = x
            _write_store(data)
        return x

def valid_callback(path, state):
    u = urllib.parse.urlsplit(path)
    q = urllib.parse.parse_qs(u.query)
    return u.path == '/oauth-callback' and len(q.get('state',[])) == 1 and hmac.compare_digest(q['state'][0], state) and (len(q.get('code',[])) == 1 or len(q.get('error',[])) == 1)

def login(timeout=300, label='Основной', no_browser=False):
    label = validate_label(label)
    cfg = public_config()
    verifier = secrets.token_urlsafe(32)
    state = secrets.token_urlsafe(32)
    challenge = __import__('base64').urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b'=').decode()
    deadline = time.monotonic()+timeout
    result: dict = {'handled':False}
    class Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self,*args): pass
        def answer(self, status, message):
            self.send_response(status)
            self.send_header('Content-Type','text/html; charset=utf-8')
            self.send_header('Cache-Control','no-store')
            self.send_header('Content-Security-Policy',"default-src 'none'; frame-ancestors 'none'")
            self.end_headers()
            self.wfile.write(('<h2>'+message+'</h2>').encode())
        def do_GET(self):
            if self.headers.get('Host') not in (f'localhost:{server.server_port}',f'127.0.0.1:{server.server_port}') or not valid_callback(self.path,state):
                self.answer(400,'Invalid callback; login remains pending.')
                return
            if result['handled'] or time.monotonic() >= deadline:
                self.answer(409,'Login expired or already processed.')
                return
            result['handled']=True
            q=urllib.parse.parse_qs(urllib.parse.urlsplit(self.path).query)
            try:
                if 'error' in q: raise RuntimeError('Google login declined')
                t=token_post(cfg, {'grant_type':'authorization_code','code':q['code'][0],'redirect_uri':cfg['redirectUri'],'code_verifier':verifier})
                if not t.get('refresh_token'): raise RuntimeError('No refresh token; login not saved')
                events=post_json(ORIGIN+'/v1internal:loadCodeAssist',t['access_token'], {'metadata':cfg['metadata']})
                p=events[0].get('cloudaicompanionProject')
                if isinstance(p,dict): p=p.get('id')
                if not isinstance(p,str) or not p.strip():
                    # New OAuth client: first login has no project yet. Mirror the
                    # Antigravity app flow — pick default allowed tier, onboardUser,
                    # then re-read loadCodeAssist for the provisioned project.
                    payload=events[0] if events else {}
                    tiers=payload.get('allowedTiers') or []
                    # The app prefers the explicit free-tier and only falls back to the
                    # default tier when free-tier is not offered at all.
                    free=next((x.get('id') for x in tiers if isinstance(x,dict) and x.get('id')=='free-tier'), None)
                    tier=free or next((x.get('id') for x in tiers if isinstance(x,dict) and x.get('isDefault')), None) or 'free-tier'
                    try:
                        onboard=post_json(ORIGIN+'/v1internal:onboardUser',t['access_token'], {'tierId':tier,'metadata':cfg['metadata']})
                        op=(onboard[0] if onboard else {}) or {}
                    except RuntimeError as oe:
                        op={'onboard_error':str(oe)[:300]}; onboard=[]
                    op_p=op.get('cloudaicompanionProject') or (op.get('response') or {}).get('cloudaicompanionProject')
                    if isinstance(op_p,dict): op_p=op_p.get('id')
                    if not (isinstance(op_p,str) and op_p.strip()):
                        events=post_json(ORIGIN+'/v1internal:loadCodeAssist',t['access_token'], {'metadata':cfg['metadata']})
                        p=events[0].get('cloudaicompanionProject')
                        if isinstance(p,dict): p=p.get('id')
                        op_p = op_p if (isinstance(op_p,str) and op_p.strip()) else p
                    p=op_p
                    try:
                        diag={'tier':tier,'tier_ids':[x.get('id') for x in tiers if isinstance(x,dict)],'ineligible':[(x.get('tierId'),(x.get('reasonMessage') or '')[:120]) for x in (payload.get('ineligibleTiers') or []) if isinstance(x,dict)],'onboard_keys':sorted(op.keys())[:10],'onboard_p':str(op_p)[:60],'onboard_error':op.get('onboard_error')}
                        with open(ROOT/'http-errors.log','a',encoding='utf-8') as f: f.write(time.strftime('%Y-%m-%d %H:%M:%S')+' ONBOARD '+json.dumps(diag,ensure_ascii=False)[:600]+'\n')
                    except OSError: pass
                    if not isinstance(p,str) or not p.strip(): raise RuntimeError('No project for account even after onboarding (tier=%s)' % tier)
                if time.monotonic() >= deadline: raise RuntimeError('Login expired')
                subject = identity(t['access_token'])
                primary_subject = None
                with store_lock():
                    primary = _read_store()['accounts'].get('primary')
                    needs_primary = primary and not primary.get('subject')
                if needs_primary:
                    primary_subject = identity(credential('primary')['accessToken'])
                record = {'accessToken':t['access_token'],'refreshToken':t['refresh_token'],'expiresAt':time.time()+int(t['expires_in']),'projectId':p}
                if time.monotonic() >= deadline: raise RuntimeError('Login expired before persistence')
                result['account_id'] = add_account(record, label, subject, primary_subject)
                self.answer(200,'Antigravity Direct connected. You can return to Hermes.')
                result['success']=True
            except Exception as exc:
                result['error']=str(exc)
                self.answer(400,'Login could not complete. Return to Hermes for status.')
    try:
        server=http.server.HTTPServer(('127.0.0.1',51121),Handler)
    except PermissionError:
        # Windows can reserve the default port; keep loopback-only without
        # changing firewall/excluded-port settings. Google desktop OAuth
        # permits a variable loopback port; exchange uses the exact same URI.
        server=http.server.HTTPServer(('127.0.0.1',0),Handler)
        cfg = dict(cfg, redirectUri=f'http://localhost:{server.server_port}/oauth-callback')
    server.timeout=0.5
    params={'client_id':cfg['clientId'],'response_type':'code','redirect_uri':cfg['redirectUri'],'scope':' '.join(cfg['scopes']),'state':state,'code_challenge':challenge,'code_challenge_method':'S256','access_type':'offline','prompt':'consent'}
    try:
        url = 'https://accounts.google.com/o/oauth2/v2/auth?' + urllib.parse.urlencode(params)
        print('Google OAuth URL: '+url, flush=True)
        if not no_browser and not webbrowser.open(url): raise RuntimeError('Could not open browser; use --no-browser')
        print('Waiting for Google login; no tokens are displayed.', flush=True)
        while not result['handled'] and time.monotonic()<deadline: server.handle_request()
        if not result.get('success'): raise RuntimeError(result.get('error','Login timeout'))
    finally: server.server_close()
    print('Connected; credential persisted with Windows DPAPI.')
    return result['account_id']

def build_request(model, messages, project, tools=None, **kwargs):
    if 'image' in model: raise ValueError('Image models are not supported on the direct route')
    contents=[]; systems=[]; names={}
    for m in messages:
        role=m['role']; text=m.get('content'); parts=[]
        if role in ('system','developer'):
            if not isinstance(text,str): raise ValueError('Only text system prompts supported')
            systems.append({'text':text}); continue
        if role == 'assistant':
            native=next((d.get('parts') for d in m.get('reasoning_details',[]) or [] if isinstance(d,dict) and d.get('type')==CARRIER),None)
            for call in m.get('tool_calls',[]) or []: names[call['id']]=call['function']['name']
            if native is not None: parts=native
            else:
                if text: parts.append({'text':text})
                for call in m.get('tool_calls',[]) or []: parts.append({'functionCall':{'name':call['function']['name'],'args':json.loads(call['function']['arguments'])}})
        elif role == 'tool':
            name=names.get(m.get('tool_call_id'))
            if not name: raise ValueError('Unmatched tool response')
            parts=[{'functionResponse':{'name':name,'response':{'result':text}}}]
        elif role == 'user':
            if not isinstance(text,str): raise ValueError('Multimodal not implemented in verification slice')
            parts=[{'text':text}]
        else: raise ValueError('Unsupported message role')
        if parts: contents.append({'role':'model' if role=='assistant' else 'user','parts':parts})
    req_sys = None
    if systems:
        sys_combined = '\n\n'.join(s['text'] for s in systems if isinstance(s, dict) and 'text' in s)
        if len(sys_combined) <= 1500:
            req_sys = {'parts': [{'text': sys_combined}]}
        else:
            if contents and contents[0]['role'] == 'user':
                for p in contents[0]['parts']:
                    if 'text' in p:
                        p['text'] = f'<system_instructions>\n{sys_combined}\n</system_instructions>\n\n' + p['text']
                        break
                else:
                    contents[0]['parts'].insert(0, {'text': f'<system_instructions>\n{sys_combined}\n</system_instructions>'})
            else:
                contents.insert(0, {'role': 'user', 'parts': [{'text': f'<system_instructions>\n{sys_combined}\n</system_instructions>'}]})
                contents.insert(1, {'role': 'model', 'parts': [{'text': 'Understood.'}]})
    req={'contents':contents,'generationConfig':{'maxOutputTokens':kwargs.get('max_tokens',8192)}}
    if req_sys: req['systemInstruction']=req_sys
    if tools: req['tools']=[{'functionDeclarations':[{'name':t['function']['name'],'description':t['function'].get('description',''),'parameters':t['function'].get('parameters',{})} for t in tools]}]
    return {'model':model,'project':project,'request':req}

def parse_events(events, model):
    parts=[]; usage={}; finish='stop'
    for e in events:
        e=e.get('response',e)
        if e.get('error'): raise RuntimeError('Antigravity response error')
        if e.get('usageMetadata'): usage=e['usageMetadata']
        for c in e.get('candidates',[]):
            parts.extend(c.get('content',{}).get('parts',[]))
            if c.get('finishReason')=='MAX_TOKENS': finish='length'
    calls=[]
    for p in parts:
        if 'functionCall' in p:
            f=p['functionCall']; calls.append({'id':'call_'+uuid.uuid4().hex[:12],'type':'function','function':{'name':f['name'],'arguments':json.dumps(f.get('args',{}))}})
    if calls: finish='tool_calls'
    message={'role':'assistant','content':''.join(p.get('text','') for p in parts if not p.get('thought')),'reasoning_details':[{'type':CARRIER,'parts':parts}]}
    if calls: message['tool_calls']=calls
    inp=usage.get('promptTokenCount',0); out=usage.get('candidatesTokenCount',0)
    return {'id':'chatcmpl-'+uuid.uuid4().hex,'object':'chat.completion','created':int(time.time()),'model':model,'choices':[{'index':0,'message':message,'finish_reason':finish}],'usage':{'prompt_tokens':inp,'completion_tokens':out,'total_tokens':usage.get('totalTokenCount',inp+out)}}

class DirectClient:
    def __init__(self, account_id='primary', **kwargs):
        from types import SimpleNamespace
        self.account_id = validate_account_id(account_id)
        self.chat=SimpleNamespace(completions=SimpleNamespace(create=self.create))
        self.api_key=LOCAL_MARKER
        self.base_url=ORIGIN
    def create(self, model, messages, stream=False, tools=None, **kwargs):
        from openai.types.chat import ChatCompletion, ChatCompletionChunk
        _dbg('create model=%s stream=%s tools=%d kw=%s' % (model, stream, len(tools or []), sorted(kwargs)))
        wire_model = route_model(model, self.account_id)
        x=credential(self.account_id)
        body=build_request(wire_model,messages,x['projectId'],tools,**kwargs)
        # NOTE: '?alt=sse' hangs indefinitely on the Antigravity endpoint (verified:
        # same body returns 200 in ~4s without it, times out with it). Request the
        # plain JSON response; parse_events() already accepts a JSON array.
        # Rate-limit patience: Google's 429 window lasts minutes, not seconds, so the
        # caller's 3x5s retry loop can never ride one out. Wait out the window here
        # (backoff 45s * attempt, 3 tries) instead of falling back to a weaker model.
        # 429 = квота аккаунта выжжена: отдаём ошибку сразу, без многоминутных пауз.
        # 429 = всплеск лимита (минутный/часовой), а не отказ аккаунта.
        # Клиенту нужен ответ, поэтому ждём и повторяем, а не отдаём ошибку.
        _waits = (8, 16, 30)
        for _i in range(len(_waits) + 1):
            try:
                events = post_json(ORIGIN + '/v1internal:streamGenerateContent', x['accessToken'], body)
                break
            except RuntimeError as _e:
                if 'HTTP 429' not in str(_e) or _i == len(_waits):
                    raise
                _w = _waits[_i]
                _dbg('429 retry in %ds (attempt %d)' % (_w, _i + 1))
                time.sleep(_w)
        parsed=parse_events(events,model)
        if not stream: return ChatCompletion.model_validate(parsed)
        # Buffered compatibility stream; true progressive streaming is not claimed.
        msg=parsed['choices'][0]['message']; delta=dict(msg)
        if delta.get('tool_calls'):
            delta['tool_calls']=[dict(c,index=i) for i,c in enumerate(delta['tool_calls'])]
        chunk={k:parsed[k] for k in ('id','created','model')}
        chunk.update(object='chat.completion.chunk',choices=[{'index':0,'delta':delta,'finish_reason':None}])
        end={**chunk,'choices':[{'index':0,'delta':{},'finish_reason':parsed['choices'][0]['finish_reason']}],'usage':parsed['usage']}
        return iter([ChatCompletionChunk.model_validate(chunk),ChatCompletionChunk.model_validate(end)])

if __name__=='__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('login','status','accounts','rename','probe'), nargs='?', default='status')
    parser.add_argument('--label', default=None)
    parser.add_argument('--account', default='primary')
    parser.add_argument('--no-browser', action='store_true')
    parser.add_argument('--timeout', type=int, default=300)
    args = parser.parse_args()
    if args.action == 'login':
        account_id = login(timeout=args.timeout, label=args.label or 'Основной', no_browser=args.no_browser)
        print('Account routing ID:', account_id)
        print('Use hermes auth add for registering the Hermes routing marker.')
    elif args.action in ('status','accounts'):
        for i,a in accounts().items(): print(i+' · '+a['label']+' · Windows DPAPI')
        if not accounts(): print('Not signed in')
    elif args.action == 'rename':
        rename_account(args.account, args.label)
        print('Label updated; restart desktop backend to refresh picker labels.')
    elif args.action == 'probe':
        r=DirectClient(account_id=args.account).create(model='gemini-3.8-flash-low', messages=[{'role':'user','content':'Reply exactly OK.'}])
        print(r.choices[0].message.content)

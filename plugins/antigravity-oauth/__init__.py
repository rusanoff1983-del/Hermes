"""Direct Antigravity model provider for Hermes Agent."""
from providers import register_provider
from providers.base import ProviderProfile
from . import direct

def auth_handler(action, args):
    if action == 'add':
        direct.login()
        _add_marker()
        return True
    if action == 'status':
        print('Antigravity Direct: ' + ('credential present (Windows DPAPI)' if direct.store_path().exists() else 'not signed in'))
        return True
    if action == 'logout':
        direct.store_path().unlink(missing_ok=True)
        from agent.credential_pool import load_pool
        pool = load_pool('antigravity-direct')
        for i in range(len(pool.entries()), 0, -1):
            pool.remove_index(i)
        print('Antigravity Direct: local credential removed (no remote revoke performed)')
        return True
    return False

def _add_marker():
    from agent.credential_pool import load_pool, PooledCredential
    import uuid
    pool = load_pool('antigravity-direct')
    if not pool.entries():
        pool.add_entry(PooledCredential(
            provider='antigravity-direct',
            id=uuid.uuid4().hex[:6],
            label='Antigravity Direct DPAPI',
            auth_type='oauth',
            priority=0,
            source='manual:direct_dpapi',
            access_token=direct.LOCAL_MARKER,
            extra={'secure_storage': 'windows-dpapi'}
        ))

class DirectProfile(ProviderProfile):
    def create_client(self, **kwargs):
        return direct.DirectClient(**kwargs)

    def fetch_models(self, **kwargs) -> list[str] | None:
        try:
            return direct.fetch_models()
        except Exception:
            return list(self.fallback_models)

profile = DirectProfile(
    name='antigravity-direct',
    display_name='Antigravity Direct',
    description='Вход через Google в браузере · прямое подключение без сторонних CLI',
    base_url=direct.ORIGIN,
    api_mode='chat_completions',
    auth_type='oauth_device_code',
    fallback_models=direct.MAINTAINED_MODELS,
    supports_health_check=False,
    supports_model_listing=True,
    native_reasoning_details_type=direct.CARRIER,
    auth_handler=auth_handler
)

register_provider(profile)

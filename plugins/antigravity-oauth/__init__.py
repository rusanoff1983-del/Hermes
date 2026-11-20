"""Profile-local Antigravity accounts: immutable provider ID selects credentials."""
from providers import register_provider
from providers.base import ProviderProfile
from . import direct


def provider_id(account_id):
    direct.validate_account_id(account_id)
    return 'antigravity-direct' if account_id == 'primary' else 'antigravity-direct-' + account_id


def auth_for(account_id):
    def handler(action, args):
        if action == 'add':
            rows = direct.accounts()
            label = getattr(args, 'label', None) or rows.get(account_id, {}).get('label', 'Основной')
            ident = direct.login(timeout=getattr(args, 'timeout', None) or 300,
                                 label=label, no_browser=bool(getattr(args, 'no_browser', False)))
            _add_marker(ident)
            register_account(ident, direct.accounts()[ident]['label'])
            return True
        if action == 'status':
            for ident, row in direct.accounts().items():
                print(provider_id(ident) + ' · ' + row['label'] + ' · Windows DPAPI')
            return True
        if action == 'logout':
            direct.remove_account(account_id)
            from agent.credential_pool import load_pool
            pool = load_pool(provider_id(account_id))
            for i in range(len(pool.entries()), 0, -1): pool.remove_index(i)
            print('Account removed locally; no remote revoke performed')
            return True
        if action == 'refresh':
            direct.credential(account_id)
            print('Account credential checked/refreshed')
            return True
        return False
    return handler


def _add_marker(account_id='primary'):
    from agent.credential_pool import load_pool, PooledCredential
    import uuid
    name = provider_id(account_id)
    pool = load_pool(name)
    if not pool.entries():
        pool.add_entry(PooledCredential(provider=name, id=uuid.uuid4().hex[:6],
            label='Antigravity Direct DPAPI', auth_type='oauth', priority=0,
            source='manual:direct_dpapi', access_token=direct.LOCAL_MARKER,
            extra={'secure_storage': 'windows-dpapi', 'account_id': account_id}))


class DirectProfile(ProviderProfile):
    account_id: str = 'primary'
    def create_client(self, **kwargs):
        kwargs.pop('account_id', None)
        return direct.DirectClient(account_id=self.account_id, **kwargs)

    def fetch_models(self, **kwargs):
        try:
            return direct.fetch_models(self.account_id)
        except Exception:
            return list(self.fallback_models)

    def discover_models(self, **kwargs):
        return [{'id': m, 'label': m, 'note': self.display_name} for m in self.fetch_models()]


def register_account(account_id, label):
    p = DirectProfile(name=provider_id(account_id),
        display_name='Antigravity Direct · ' + label,
        description='Google OAuth · отдельный аккаунт · прямое подключение без agy',
        base_url=direct.ORIGIN, api_mode='chat_completions', auth_type='oauth_device_code',
        fallback_models=direct.MAINTAINED_MODELS,
        supports_health_check=False, supports_model_listing=True,
        native_reasoning_details_type=direct.CARRIER, auth_handler=auth_for(account_id))
    p.account_id = account_id
    register_provider(p)
    return p


_rows = direct.accounts()
profile = register_account('primary', _rows.get('primary', {}).get('label', 'Основной'))
for _ident, _row in _rows.items():
    if _ident != 'primary': register_account(_ident, _row['label'])
auth_handler = auth_for('primary')

#!/usr/bin/env python3
"""Install the Favorites UI and its native Desktop bridge; Python stdlib only."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent
CORE_PATHS = [
    'apps/desktop/src/sdk/index.ts',
    'apps/desktop/src/sdk/models.ts',
    'apps/desktop/src/sdk/models.test.ts',
    'apps/desktop/src/app/model-picker-overlay.tsx',
    'apps/desktop/src/app/model-picker-overlay.test.tsx',
]

def default_home():
    if os.environ.get('HERMES_HOME'):
        return Path(os.environ['HERMES_HOME']).expanduser()
    if sys.platform == 'win32':
        return Path(os.environ.get('LOCALAPPDATA', Path.home() / 'AppData/Local')) / 'hermes'
    return Path.home() / '.hermes'

def run(args, cwd, capture=False, check=True):
    args = list(map(str, args))
    # Windows .cmd launchers are not directly executable with shell=False.
    executable = shutil.which(args[0])
    if not executable:
        raise RuntimeError(f'Required command not found: {args[0]}')
    args[0] = executable
    if sys.platform == 'win32' and executable.lower().endswith(('.cmd', '.bat')):
        args = ['cmd.exe', '/d', '/s', '/c', subprocess.list2cmdline(args)]
    return subprocess.run(args, cwd=cwd, check=check, text=True, encoding='utf-8',
                          errors='replace', capture_output=capture)

def bridge_state(source):
    patch = ROOT / 'native-model-selection.patch'
    if not patch.is_file():
        patch = ROOT / 'interface/native-model-selection.patch'
    if run(['git', 'apply', '--reverse', '--check', patch], source, True, False).returncode == 0:
        return 'installed'
    checked = run(['git', 'apply', '--check', patch], source, True, False)
    if checked.returncode:
        raise RuntimeError('Interface version/conflicting edits are incompatible. No files changed.\n' + checked.stderr)
    return 'ready'

def backup_file(target, backup, receipt):
    entry = {'target': str(target), 'backup': None}
    if target.exists():
        backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(target, backup)
        entry['backup'] = str(backup)
    receipt['files'].append(entry)

def copy_verified(source, target):
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    if hashlib.sha256(source.read_bytes()).digest() != hashlib.sha256(target.read_bytes()).digest():
        raise RuntimeError(f'Copy verification failed: {target}')

def renderer_files(dist):
    excluded = {'electron-main.mjs', 'electron-preload.js', 'preview-guest-preload.js', 'install-stamp.json'}
    files = [p for p in dist.rglob('*') if p.is_file() and
             p.relative_to(dist).parts[0] not in {'node_modules', 'native'} and p.name not in excluded]
    return sorted(files, key=lambda p: p.name == 'index.html')

def deploy_renderer(dist, target, backup, receipt):
    if not (dist / 'index.html').is_file() or not (target / 'index.html').is_file():
        raise RuntimeError('Built renderer or unpacked Desktop renderer is absent. No renderer deployed.')
    # Preserve old hashed chunks for any still-running window; install index last.
    for file in renderer_files(dist):
        rel = file.relative_to(dist)
        dest = target / rel
        backup_file(dest, backup / 'renderer' / rel, receipt)
        copy_verified(file, dest)
    refs = re.findall(r'(?:src|href)="\.?/?(assets/[^"?#]+)', (target / 'index.html').read_text(encoding='utf-8'))
    if not refs or any(not (target / ref).is_file() for ref in refs):
        raise RuntimeError('Renderer asset reference verification failed')
    receipt['renderer'] = str(target)
    receipt['renderer_references_verified'] = len(refs)

def rollback(receipt_file):
    data = json.loads(receipt_file.read_text(encoding='utf-8'))
    # Refuse to overwrite a file modified since installation.
    for entry in data['files']:
        target = Path(entry['target'])
        if 'installed_sha256' in entry and target.exists():
            actual = hashlib.sha256(target.read_bytes()).hexdigest()
            if actual != entry['installed_sha256']:
                raise RuntimeError(f'Rollback conflict: {target} changed after installation')
    for entry in reversed(data['files']):
        target = Path(entry['target'])
        if entry['backup']:
            copy_verified(Path(entry['backup']), target)
        elif target.exists():
            target.unlink()
    print('Rollback complete. Reload Desktop. Credentials and chats were not touched.')

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--hermes-home', type=Path, default=default_home())
    parser.add_argument('--source', type=Path, help='Hermes git source checkout; defaults to HERMES_HOME/hermes-agent')
    parser.add_argument('--renderer-dir', type=Path, help='Optional unpacked packaged Desktop dist directory')
    parser.add_argument('--install-deps', action='store_true', help='Run npm ci at upstream root before building')
    parser.add_argument('--check', action='store_true', help='Read-only compatibility check')
    parser.add_argument('--rollback', type=Path, help='Restore files from a prior receipt, refusing later edits')
    args = parser.parse_args()
    if args.rollback:
        rollback(args.rollback.resolve())
        return
    home = args.hermes_home.expanduser().resolve()
    source = (args.source or home / 'hermes-agent').expanduser().resolve()
    if not (source / '.git').exists() or not (source / 'apps/desktop/package.json').exists():
        raise RuntimeError('A Hermes source/git installation with Desktop is required. Use --source PATH; MSIX-only installs are not supported by this bridge installer.')
    state = bridge_state(source)
    commit = run(['git', 'rev-parse', 'HEAD'], source, True).stdout.strip()
    print(f'Home: {home}\nSource: {source}\nUpstream revision: {commit}\nBridge: {state}')
    if args.check:
        print('Compatible. Check only: nothing written.')
        return
    if not shutil.which('npm'):
        raise RuntimeError('Node.js/npm is required to rebuild the interface. Install Node.js 22.22+ or 24.11+ first.')
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    backup = home / 'customizations/Hermes-monorepo/backups' / stamp
    backup.mkdir(parents=True)
    receipt = {'upstream_revision': commit, 'bridge_state_before': state, 'files': []}
    receipt_path = backup / 'receipt.json'
    try:
        if state == 'ready':
            for path in CORE_PATHS:
                backup_file(source / path, backup / 'core' / path, receipt)
            patch = ROOT / 'native-model-selection.patch'
            if not patch.is_file():
                patch = ROOT / 'interface/native-model-selection.patch'
            run(['git', 'apply', patch], source)
        if args.install_deps:
            run(['npm', 'ci'], source)
        desktop = source / 'apps/desktop'
        run(['npx', 'vitest', 'run', '--project', 'ui', 'src/sdk/models.test.ts',
             'src/app/model-picker-overlay.test.tsx', 'src/app/session/hooks/use-model-controls.test.tsx'], desktop)
        run(['npx', 'tsc', '-p', 'tsconfig.json', '--noEmit'], desktop)
        run(['npm', 'run', 'build'], desktop)
        target = args.renderer_dir
        candidate = desktop / 'release/win-unpacked/resources/app.asar.unpacked/dist'
        if target is None and candidate.is_dir():
            target = candidate
        if target:
            deploy_renderer(desktop / 'dist', target.resolve(), backup, receipt)
        plugin = home / 'desktop-plugins/favorites-models/plugin.js'
        backup_file(plugin, backup / 'plugin.js', receipt)
        plugin_src = ROOT / 'plugin.js' if (ROOT / 'plugin.js').is_file() else ROOT / 'plugins/favorites-models/plugin.js'
        copy_verified(plugin_src, plugin)
        for entry in receipt['files']:
            target_file = Path(entry['target'])
            if target_file.is_file():
                entry['installed_sha256'] = hashlib.sha256(target_file.read_bytes()).hexdigest()
        receipt['status'] = 'installed'
        print(f'Installed. Backup/rollback receipt: {receipt_path}')
        if 'renderer' in receipt:
            print('Reload the Desktop window to activate the native bridge. No backend restart required.')
        else:
            print('Built source Desktop. Launch that build with: cd <source>/apps/desktop && npm exec electron .')
            print('A separate MSIX/AppImage/.app installation was NOT patched.')
    except Exception:
        # Preserve partial progress for rollback; never call a failed build installed.
        receipt['status'] = 'failed'
        raise
    finally:
        receipt_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding='utf-8')

if __name__ == '__main__':
    try:
        main()
    except (RuntimeError, subprocess.CalledProcessError, OSError) as error:
        print(f'ERROR: {error}', file=sys.stderr)
        sys.exit(1)

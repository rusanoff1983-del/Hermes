import importlib.util
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('installer', Path(__file__).resolve().parents[1] / 'install.py')
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)

class InstallerTests(unittest.TestCase):
    def test_copy_hash_verified(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            src = root / 'source'; src.write_bytes(b'actual artifact')
            dst = root / 'nested/target'
            installer.copy_verified(src, dst)
            self.assertEqual(src.read_bytes(), dst.read_bytes())

    def test_renderer_deployment_and_rollback(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); src = root / 'dist'; dst = root / 'target'
            (src / 'assets').mkdir(parents=True); (dst / 'assets').mkdir(parents=True)
            (src / 'index.html').write_text('<script src="./assets/new.js"></script>')
            (src / 'assets/new.js').write_text('new renderer')
            (src / 'electron-main.mjs').write_text('must not replace main')
            (dst / 'index.html').write_text('original index')
            (dst / 'electron-main.mjs').write_text('original main')
            (dst / 'assets/old.js').write_text('old chunk')
            receipt = {'files': []}
            installer.deploy_renderer(src, dst, root / 'backup', receipt)
            self.assertEqual((dst / 'index.html').read_text(), (src / 'index.html').read_text())
            self.assertEqual((dst / 'electron-main.mjs').read_text(), 'original main')
            self.assertTrue((dst / 'assets/old.js').exists())
            self.assertEqual(receipt['renderer_references_verified'], 1)
            file = root / 'receipt.json'
            file.write_text(installer.json.dumps(receipt))
            installer.rollback(file)
            self.assertEqual((dst / 'index.html').read_text(), 'original index')
            self.assertFalse((dst / 'assets/new.js').exists())

    def test_rollback_refuses_later_edits(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); target = root / 'plugin.js'; target.write_text('modified later')
            file = root / 'receipt.json'
            file.write_text(installer.json.dumps({'files':[{'target':str(target),'backup':None,'installed_sha256':'different'}]}))
            with self.assertRaisesRegex(RuntimeError, 'Rollback conflict'):
                installer.rollback(file)
            self.assertEqual(target.read_text(), 'modified later')

if __name__ == '__main__': unittest.main()

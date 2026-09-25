import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from deploy.configure import configure


class DeploymentConfigTests(unittest.TestCase):
    def test_default_is_loopback_and_utc(self):
        with tempfile.TemporaryDirectory() as folder, patch('deploy.configure.socket.socket') as socket:
            config = configure(folder)
            self.assertEqual(config['host'],'127.0.0.1')
            self.assertEqual(config['timezone'],'UTC')
            self.assertEqual(config['allowed_networks'],['127.0.0.0/8'])
            socket.return_value.__enter__.return_value.bind.assert_called_once_with(('127.0.0.1',8790))

    def test_explicit_network_and_home_paths(self):
        with tempfile.TemporaryDirectory() as folder, patch('deploy.configure.socket.socket'):
            config = configure(folder,'192.168.1.100','192.168.1.0/24','Europe/London',8800)
            self.assertEqual(config['port'],8800)
            self.assertEqual(config['timezone'],'Europe/London')
            self.assertIn('192.168.1.100',config['allowed_hosts'])
            self.assertEqual(config['codex'],str(Path(folder)/'runtime/node_modules/.bin/codex'))
            self.assertEqual(json.loads((Path(folder)/'config.json').read_text()),config)

    def test_existing_configuration_is_preserved(self):
        with tempfile.TemporaryDirectory() as folder, patch('deploy.configure.socket.socket') as socket:
            path=Path(folder)/'config.json'
            original={'host':'192.168.1.50','timezone':'Europe/Paris','custom':'preserve'}
            path.write_text(json.dumps(original))
            before=path.read_bytes()
            self.assertEqual(configure(folder),original)
            self.assertEqual(path.read_bytes(),before)
            socket.assert_not_called()

    def test_invalid_network_settings_never_create_config(self):
        cases=[('0.0.0.0','0.0.0.0/0','UTC',8790),
               ('192.168.1.100','10.0.0.0/8','UTC',8790),
               ('192.168.1.100','192.168.1.0/24','UTC',80)]
        for args in cases:
            with self.subTest(args=args), tempfile.TemporaryDirectory() as folder:
                with self.assertRaises(ValueError): configure(folder,*args)
                self.assertFalse((Path(folder)/'config.json').exists())

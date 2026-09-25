import http.client
from pathlib import Path
import tempfile
import threading
import unittest

from metrics import Store
from monitor import BoundedServer, handler_for


class HttpTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.store = Store(Path(self.folder.name)/'test.sqlite')
        self.config = dict(allowed_networks=['127.0.0.0/8'],allowed_hosts=['127.0.0.1'],
                           timezone='America/Los_Angeles',stale_seconds=900,poll_seconds=300,demo=False)
        self.server = BoundedServer(('127.0.0.1',0),handler_for(self.store,self.config))
        self.thread = threading.Thread(target=self.server.serve_forever,daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown();self.server.server_close();self.thread.join()
        self.folder.cleanup()

    def request(self, path, headers=None, method='GET'):
        client = http.client.HTTPConnection('127.0.0.1',self.server.server_port,timeout=3)
        client.request(method,path,headers=headers or {})
        response = client.getresponse()
        output = response.status,response.read(),dict(response.getheaders())
        client.close()
        return output

    def test_static_and_api(self):
        status,body,headers = self.request('/api/status')
        self.assertEqual(status,200)
        self.assertIn(b'"state": "unavailable"',body)
        self.assertIn('no-store',headers['Cache-Control'])
        self.assertEqual(self.request('/')[0],200)
        self.assertEqual(self.request('/api/display')[0],200)

    def test_rebinding_origin_traversal_and_mutation_rejected(self):
        self.assertEqual(self.request('/api/status',{'Host':'attacker.example'})[0],403)
        self.assertEqual(self.request('/api/status',{'Origin':'https://attacker.example'})[0],403)
        self.assertEqual(self.request('/../discovery.py')[0],404)
        self.assertEqual(self.request('/api/status',method='POST')[0],501)


if __name__ == '__main__':
    unittest.main()

"""Read-only LAN dashboard and low-frequency account collector."""
import argparse
import asyncio
import ipaddress
import json
import os
from pathlib import Path
import signal
import socketserver
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
import time
from urllib.parse import urlsplit

from discovery import probe
from metrics import Store

ROOT = Path(__file__).resolve().parent


def load_config(path):
    config = json.loads(Path(path).read_text(encoding='utf-8'))
    defaults = {'host': '127.0.0.1', 'port': 8790, 'timezone': 'UTC',
                'poll_seconds': 300, 'stale_seconds': 900, 'allowed_networks': ['127.0.0.0/8'],
                'allowed_hosts': ['localhost', '127.0.0.1'], 'database': 'data/usage.sqlite',
                'codex': 'codex', 'demo': False}
    if set(config)-set(defaults):
        raise ValueError('Unknown configuration field')
    defaults.update(config)
    from zoneinfo import ZoneInfo
    ZoneInfo(defaults['timezone'])
    if not 60 <= defaults['poll_seconds'] <= 3600:
        raise ValueError('poll_seconds must be 60–3600')
    if not defaults['poll_seconds']*2 <= defaults['stale_seconds'] <= 7200:
        raise ValueError('Invalid stale_seconds')
    if not 1024 <= defaults['port'] <= 65535:
        raise ValueError('Invalid port')
    ipaddress.ip_address(defaults['host'])
    for network in defaults['allowed_networks']:
        ipaddress.ip_network(network)
    return defaults


def collect(store, config, stop):
    failures = 0
    while not stop.is_set():
        try:
            result = asyncio.run(probe([config['codex'], 'app-server'], timeout=30,
                                      include_tokens=True, diagnostics=True, track_account=True))
            store.record(result)
            failures = 0 if result.get('status') == 'ok' else failures+1
        except Exception:
            # Never log exception text that might carry credentials/upstream bodies.
            store.record({'status': 'collector_error'})
            failures += 1
        stop.wait(min(3600, config['poll_seconds'] * 2**min(failures, 3)))


def seed_demo(store, now):
    from datetime import datetime, timezone
    reset = int(now+2*86400)
    for n in range(5*24*12+1):
        ts = now - (5*24*12-n)*300
        store.record({'status': 'ok', 'account_fingerprint': 'demo',
            'weekly_observed_at': datetime.fromtimestamp(ts, timezone.utc).isoformat(),
            'tokens_observed_at': datetime.fromtimestamp(ts, timezone.utc).isoformat(),
            'weekly': {'used_percent': min(89, 20+n*69/(5*24*12)),
                       'resets_at': datetime.fromtimestamp(reset, timezone.utc).isoformat()},
            'token_summary': {'lifetimeTokens': 8_000_000_000+n*350_000},
            'token_status': 'demo'}, now=now)


def handler_for(store, config):
    networks = [ipaddress.ip_network(n) for n in config['allowed_networks']]
    assets = {'/': ('index.html', 'text/html; charset=utf-8'),
              '/app.js': ('app.js', 'text/javascript; charset=utf-8'),
              '/style.css': ('style.css', 'text/css; charset=utf-8')}

    class Handler(BaseHTTPRequestHandler):
        server_version = 'CodexMeter/1'

        def setup(self):
            super().setup()
            self.connection.settimeout(5)

        def log_message(self, *args):
            pass

        def send_body(self, code, body, content_type):
            self.send_response(code)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Referrer-Policy', 'no-referrer')
            self.send_header('Content-Security-Policy', "default-src 'self'; style-src 'self'; script-src 'self'; connect-src 'self'; frame-ancestors 'none'")
            self.end_headers()
            self.wfile.write(body)

        def allowed(self):
            try:
                address = ipaddress.ip_address(self.client_address[0])
                host = urlsplit('//'+self.headers.get('Host', '')).hostname
                if not any(address in n for n in networks) or host not in config['allowed_hosts']:
                    return False
                origin = self.headers.get('Origin')
                return not origin or origin == 'http://'+self.headers.get('Host')
            except ValueError:
                return False

        def do_GET(self):
            if not self.allowed():
                self.send_body(403, b'Forbidden', 'text/plain')
                return
            path = urlsplit(self.path).path
            if path in ('/api/status', '/api/display'):
                output = store.status(tz=config['timezone'], stale_seconds=config['stale_seconds'],
                                      poll_seconds=config['poll_seconds'])
                output['demo'] = config['demo']
                output['poll_seconds'] = config['poll_seconds']
                output['stale_seconds'] = config['stale_seconds']
                if path == '/api/display':
                    output.pop('reported_daily_tokens', None)
                    output.pop('reported_daily_scope', None)
                    output.pop('last_attempt', None)
                self.send_body(200, json.dumps(output, allow_nan=False).encode(), 'application/json')
            elif path == '/healthz':
                self.send_body(200, b'{"ok":true}', 'application/json')
            elif path in assets:
                name, kind = assets[path]
                self.send_body(200, (ROOT/'web'/name).read_bytes(), kind)
            else:
                self.send_body(404, b'Not found', 'text/plain')

    return Handler


class BoundedServer(socketserver.ThreadingMixIn, HTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, *args):
        self.slots = threading.BoundedSemaphore(12)
        super().__init__(*args)

    def process_request(self, request, address):
        if not self.slots.acquire(blocking=False):
            request.close()
            return
        try:
            super().process_request(request, address)
        except Exception:
            self.slots.release()
            raise

    def process_request_thread(self, *args):
        try:
            super().process_request_thread(*args)
        finally:
            self.slots.release()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', default='config.local.json')
    parser.add_argument('--once', action='store_true')
    args = parser.parse_args()
    config = load_config(args.config)
    db = Path(config['database']).expanduser().resolve()
    db.parent.mkdir(parents=True, exist_ok=True)
    os.umask(0o077)
    store = Store(db)
    if args.once:
        store.record(asyncio.run(probe([config['codex'], 'app-server'], include_tokens=True,
                                       diagnostics=True, track_account=True)))
        print(json.dumps(store.status(tz=config['timezone']), indent=2))
        return
    stop = threading.Event()
    server = BoundedServer((config['host'], config['port']), handler_for(store, config))
    if config['demo']:
        seed_demo(store, time.time())
    else:
        threading.Thread(target=collect, args=(store, config, stop), daemon=True).start()
    def shutdown(*_):
        stop.set()
        threading.Thread(target=server.shutdown, daemon=True).start()
    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)
    print(f"Dashboard listening on {config['host']}:{config['port']}", flush=True)
    try:
        server.serve_forever(poll_interval=0.5)
    finally:
        stop.set()
        server.server_close()


if __name__ == '__main__':
    main()

"""Create first-install settings; never overwrite an existing installation."""
import ipaddress
import json
from pathlib import Path
import socket
import sys
from zoneinfo import ZoneInfo


def configure(base, host='127.0.0.1', network='127.0.0.0/8', timezone='UTC', port=8790):
    base = Path(base)
    path = base/'config.json'
    if path.exists():
        return json.loads(path.read_text(encoding='utf-8'))
    address = ipaddress.IPv4Address(host)
    allowed = ipaddress.IPv4Network(network)
    if address.is_unspecified or address.is_multicast or not (address.is_private or address.is_loopback):
        raise ValueError('Use a specific private or loopback IPv4 address')
    if address not in allowed:
        raise ValueError('Allowed network must include the server for local verification')
    ZoneInfo(timezone)
    port = int(port)
    if not 1024 <= port <= 65535:
        raise ValueError('Port must be 1024-65535')
    with socket.socket() as sock:
        sock.bind((host, port))
    config = dict(host=host, port=port, database=str(base/'data/usage.sqlite'),
                  codex=str(base/'runtime/node_modules/.bin/codex'), timezone=timezone,
                  poll_seconds=300, stale_seconds=900,
                  allowed_networks=list(dict.fromkeys(['127.0.0.0/8',network])),
                  allowed_hosts=list(dict.fromkeys([host,'localhost','127.0.0.1'])),demo=False)
    base.mkdir(parents=True,exist_ok=True)
    with path.open('x',encoding='utf-8') as output:
        json.dump(config,output,indent=2)
    return config


if __name__ == '__main__':
    configure(*sys.argv[1:])

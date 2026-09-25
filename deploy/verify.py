"""Local-on-Ubuntu verification. Prints only public dashboard fields."""
import argparse
import json
from pathlib import Path
import time
import urllib.request

parser=argparse.ArgumentParser()
parser.add_argument('--wait',type=int,default=30)
parser.add_argument('--after',type=float,default=0)
parser.add_argument('--config', required=True)
args=parser.parse_args()
config=json.loads(Path(args.config).read_text(encoding='utf-8'))
base_url=f"http://{config['host']}:{config['port']}"
deadline=time.monotonic()+args.wait
while True:
    try:
        with urllib.request.urlopen(base_url+'/api/status',timeout=5) as response:
            result=json.load(response)
        if (result['state']=='fresh' and not result.get('demo', True)
                and result.get('updated_at', 0)>args.after
                and result.get('last_attempt',{}).get('status')=='ok'):
            with urllib.request.urlopen(base_url+'/api/display',timeout=5) as response:
                compact=response.read()
            assert len(compact)<16384, 'Display payload too large'
            print(json.dumps({'verification':'ok','state':result['state'],'weekly':result['weekly'],
                'updated_at':result['updated_at'],'token_status':result['token_status'],
                'reported_daily_bucket_count':len(result.get('reported_daily_tokens',[])),
                'display_payload_bytes':len(compact),'demo':result['demo']},indent=2))
            break
    except (OSError,ValueError,KeyError):
        pass
    if time.monotonic()>=deadline:
        raise SystemExit('Service did not produce a fresh successful reading within the verification window.')
    time.sleep(2)

"""Create a deterministic source-only deployment archive; exclude all local data."""
import hashlib
from pathlib import Path
import zipfile

root=Path(__file__).resolve().parents[1]
files=[root/name for name in ('monitor.py','metrics.py','discovery.py')]
for folder in ('web','tests','deploy'):
    files.extend(p for p in (root/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts)
destination=root/'dist/codex-usage-monitor.zip'
destination.parent.mkdir(exist_ok=True)
with zipfile.ZipFile(destination,'w',zipfile.ZIP_DEFLATED) as archive:
    for path in sorted(files):
        content=path.read_bytes()
        if path.suffix in ('.py','.sh','.js','.css','.html'):
            content=content.replace(b'\r\n',b'\n')
        info=zipfile.ZipInfo(path.relative_to(root).as_posix(),date_time=(2026,1,1,0,0,0))
        info.compress_type=zipfile.ZIP_DEFLATED
        archive.writestr(info,content)
print(f'{destination.name}: {len(files)} files, {destination.stat().st_size} bytes')
print('SHA256 '+hashlib.sha256(destination.read_bytes()).hexdigest())

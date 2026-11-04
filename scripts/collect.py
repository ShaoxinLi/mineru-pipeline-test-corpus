"""Download pinned public fixtures and verify their Git blob identities."""
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha1
import json
from pathlib import Path
import time
from urllib.parse import quote
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]


def download(url: str) -> bytes:
    for attempt in range(3):
        try:
            with urlopen(url, timeout=40) as response:
                if response.status != 200:
                    raise ValueError(f"HTTP {response.status}: {url}")
                return response.read()
        except Exception:
            if attempt == 2:
                raise
            time.sleep(attempt + 1)
    raise AssertionError("unreachable")


def collect(item: dict) -> str:
    url = f"https://raw.githubusercontent.com/{item['repository']}/{item['commit']}/{quote(item['source_path'])}"
    content = download(url)
    digest = sha1(b"blob " + str(len(content)).encode() + b"\0" + content).hexdigest()
    assert digest == item['source_git_blob_sha'], f"Git blob mismatch: {item['id']}"
    assert len(content) == item['source_size'], item['id']
    path = ROOT / item['path']
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return item['id']


def main() -> None:
    config = json.loads((ROOT / 'sources.json').read_text())
    with ThreadPoolExecutor(max_workers=6) as pool:
        for sample_id in pool.map(collect, config['sources']):
            print(sample_id, flush=True)
    repos = {item['origin']: item for item in config['sources']}
    for name, paths in {'markitdown': ['LICENSE'], 'tika': ['LICENSE.txt', 'NOTICE.txt']}.items():
        item = repos[name]
        for source_path in paths:
            content = download(f"https://raw.githubusercontent.com/{item['repository']}/{item['commit']}/{source_path}")
            path = ROOT / 'licenses' / name / source_path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
    print('Downloaded and verified', len(config['sources']), 'fixtures.')


if __name__ == '__main__':
    main()

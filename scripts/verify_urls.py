"""Check anonymous raw downloads against the manifest; never calls a parsing API."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]


def verify(item: dict) -> dict:
    error = ''
    for attempt in range(3):
        try:
            request = Request(item['url'], headers={'User-Agent': 'mineru-test-corpus-url-verifier/1'})
            with urlopen(request, timeout=45) as response:
                content = response.read()
                actual_hash = hashlib.sha256(content).hexdigest()
                assert response.status == 200, f'HTTP {response.status}'
                assert len(content) == item['validation']['bytes'], 'size mismatch'
                assert actual_hash == item['validation']['sha256'], 'SHA-256 mismatch'
                return {'id': item['id'], 'url': item['url'], 'ok': True, 'status': response.status,
                        'bytes': len(content), 'sha256': actual_hash,
                        'content_type': response.headers.get('Content-Type'), 'final_url': response.url}
        except Exception as exc:
            error = str(exc)
            if attempt < 2:
                time.sleep(attempt + 1)
    return {'id': item['id'], 'url': item['url'], 'ok': False, 'error': error}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--smoke', action='store_true', help='Only one sample per extension')
    parser.add_argument('--output', default='verification/remote.json')
    args = parser.parse_args()
    manifest = json.loads((ROOT / 'manifest.json').read_text())
    entries = [x for x in manifest['samples'] if not args.smoke or x['smoke']]
    with ThreadPoolExecutor(max_workers=6) as pool:
        results = list(pool.map(verify, entries))
    report = {'checked_at_utc': datetime.now(timezone.utc).isoformat(), 'sample_commit': manifest['sample_commit'],
              'verification_origin': 'machine_running_this_script', 'authentication': 'none',
              'checks': ['HTTP 200', 'exact byte count', 'SHA-256 matches local validated file'],
              'pipeline_execution': 'not_run', 'passed': sum(x['ok'] for x in results), 'total': len(results), 'results': results}
    path = ROOT / args.output
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(f"Verified {report['passed']}/{report['total']} anonymous download URLs; wrote {path}")
    for result in results:
        if not result['ok']:
            print(result['id'], result['error'])
    raise SystemExit(0 if all(x['ok'] for x in results) else 1)


if __name__ == '__main__':
    main()

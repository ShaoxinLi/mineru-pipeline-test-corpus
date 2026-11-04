"""Stream anonymous downloads and check integrity without retaining large files."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import time
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]


def verify(item: dict) -> dict:
    error = ''
    for attempt in range(3):
        try:
            digest = sha256()
            count = 0
            started = time.monotonic()
            request = Request(item['url'], headers={'Accept-Encoding': 'identity', 'User-Agent': 'mineru-boundary-verifier/1'})
            with urlopen(request, timeout=60) as response:
                assert response.status == 200, response.status
                while chunk := response.read(1024 * 1024):
                    count += len(chunk)
                    digest.update(chunk)
                    assert count <= item['bytes'], 'received too many bytes'
                assert count == item['bytes'], (count, item['bytes'])
                assert digest.hexdigest() == item['sha256'], 'SHA-256 mismatch'
                result = {'id': item['id'], 'url': item['url'], 'ok': True, 'status': response.status,
                          'bytes': count, 'sha256': digest.hexdigest(), 'seconds': round(time.monotonic() - started, 3),
                          'final_host': urlsplit(response.url).hostname}
                print(item['id'], 'verified', count, 'bytes', flush=True)
                return result
        except Exception as exc:
            error = str(exc)
            if attempt < 2:
                time.sleep(attempt + 1)
    print(item['id'], 'FAILED', error, flush=True)
    return {'id': item['id'], 'url': item['url'], 'ok': False, 'error': error}


def main() -> None:
    manifest = json.loads((ROOT / 'boundary/manifest.json').read_text())
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(verify, manifest['samples']))
    report = {'checked_at_utc': datetime.now(timezone.utc).isoformat(), 'verification_origin': 'machine_running_this_script',
              'authentication': 'none', 'pipeline_execution': 'not_run', 'passed': sum(x['ok'] for x in results),
              'total': len(results), 'results': results}
    (ROOT / 'boundary/verification.json').write_text(json.dumps(report, indent=2) + '\n')
    print(f"Verified {report['passed']}/{report['total']} URLs")
    raise SystemExit(0 if all(x['ok'] for x in results) else 1)


if __name__ == '__main__':
    main()

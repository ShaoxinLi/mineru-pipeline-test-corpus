"""Keep the complete URL list in sync with both sample manifests."""
import json
from pathlib import Path


def update_url_lists(root: Path) -> None:
    regular = json.loads((root / 'manifest.json').read_text())['samples']
    boundary_manifest = root / 'boundary/manifest.json'
    boundary = json.loads(boundary_manifest.read_text())['samples'] if boundary_manifest.exists() else []
    urls = [sample['url'] for sample in regular + boundary]
    if len(set(urls)) != len(urls):
        raise ValueError('Duplicate sample URLs in the manifests')
    (root / 'urls_regular.txt').write_text(''.join(sample['url'] + '\n' for sample in regular))
    (root / 'urls.txt').write_text(''.join(url + '\n' for url in urls))


if __name__ == '__main__':
    update_url_lists(Path(__file__).resolve().parents[1])

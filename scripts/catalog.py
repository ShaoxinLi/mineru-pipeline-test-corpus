"""Validate local files, then publish a machine-readable, commit-pinned catalog."""
import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import quote
import xml.etree.ElementTree as ET
from zipfile import ZipFile

from update_url_lists import update_url_lists

import olefile
from PIL import Image
import pypdfium2 as pdfium

ROOT = Path(__file__).resolve().parents[1]
OFFICIAL = set('pdf png jpg jpeg webp gif bmp jp2 doc docx ppt pptx xls xlsx html'.split())
IMAGE_FORMATS = {'png': 'PNG', 'jpg': 'JPEG', 'jpeg': 'JPEG', 'webp': 'WEBP', 'gif': 'GIF', 'bmp': 'BMP', 'jp2': 'JPEG2000'}
SMOKE = {
    'pdf': 'markitdown_pdf_receipt', 'png': 'receipt_baseline_png', 'jpg': 'receipt_baseline_jpg',
    'jpeg': 'receipt_baseline_jpeg', 'webp': 'receipt_baseline_webp', 'gif': 'receipt_baseline_gif',
    'bmp': 'receipt_baseline_bmp', 'jp2': 'receipt_baseline_jp2', 'doc': 'tika_word_legacy',
    'docx': 'markitdown_word_baseline', 'ppt': 'tika_slides_legacy', 'pptx': 'markitdown_slides_baseline',
    'xls': 'markitdown_spreadsheet_legacy', 'xlsx': 'markitdown_spreadsheet_modern',
    'html': 'synthetic_bilingual_report_html', 'md': 'synthetic_bilingual_report_md',
    'txt': 'synthetic_bilingual_report_txt', 'rst': 'synthetic_bilingual_report_rst',
    'tex': 'synthetic_bilingual_report_tex',
}


def validate(item: dict) -> dict:
    path = ROOT / item['path']
    data = path.read_bytes()
    assert 0 < len(data) < 200 * 1024 * 1024, path
    assert not data.startswith(b'version https://git-lfs.github.com/spec/'), path
    result = {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
    ext = item['extension']
    if ext in IMAGE_FORMATS:
        with Image.open(path) as image:
            assert image.format == IMAGE_FORMATS[ext], path
            result.update(width=image.width, height=image.height, frames=getattr(image, 'n_frames', 1))
            image.load()
    elif ext == 'pdf':
        assert data.startswith(b'%PDF-'), path
        doc = pdfium.PdfDocument(path)
        chars = []
        try:
            assert 0 < len(doc) <= 200, path
            for i in range(len(doc)):
                page = doc[i]
                text = page.get_textpage()
                chars.append(len(text.get_text_range()))
                text.close()
                page.close()
            result.update(pages=len(doc), text_layer_characters=sum(chars))
        finally:
            doc.close()
    elif ext in {'docx', 'pptx', 'xlsx'}:
        with ZipFile(path) as archive:
            assert archive.testzip() is None, path
            root = {'docx': 'word/document.xml', 'pptx': 'ppt/presentation.xml', 'xlsx': 'xl/workbook.xml'}[ext]
            ET.fromstring(archive.read(root))
            ET.fromstring(archive.read('[Content_Types].xml'))
            names = archive.namelist()
            assert not any('vbaProject' in name for name in names), path
            if ext == 'docx':
                document_xml = archive.read(root)
                result['math_elements'] = document_xml.count(b'<m:oMath>')
                result['tables'] = document_xml.count(b'<w:tbl>')
            elif ext == 'pptx':
                result['slides'] = sum(bool(re.fullmatch(r'ppt/slides/slide\d+\.xml', name)) for name in names)
            else:
                result['worksheets'] = sum(bool(re.fullmatch(r'xl/worksheets/sheet\d+\.xml', name)) for name in names)
    elif ext in {'doc', 'ppt', 'xls'}:
        assert olefile.isOleFile(path), path
        with olefile.OleFileIO(path) as ole:
            streams = ole.listdir()
            required = {'doc': ['WordDocument'], 'ppt': ['PowerPoint Document'], 'xls': ['Workbook', 'Book']}[ext]
            assert any(ole.exists(name) for name in required), path
            assert not any('vba' in part.lower() for stream in streams for part in stream), path
            result['ole_streams'] = len(streams)
    else:
        encoding = 'gb18030' if 'gb18030' in item['id'] else 'utf-8-sig'
        decoded = data.decode(encoding)
        result['encoding'] = encoding
        for anchor in item.get('expected_text_contains', []):
            assert anchor in decoded, (path, anchor)
        if ext == 'html':
            assert '<!doctype html>' in decoded.lower() and '</html>' in decoded.lower(), path
    return result


def write_json(path: str, data: object) -> None:
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--ref', help='40-character commit containing the samples; omit for validation only')
    parser.add_argument('--repository', default='ShaoxinLi/mineru-pipeline-test-corpus')
    args = parser.parse_args()
    if args.ref and not re.fullmatch('[0-9a-f]{40}', args.ref):
        parser.error('--ref must be a full 40-character commit')
    config = json.loads((ROOT / 'sources.json').read_text())
    entries = config['sources'] + json.loads((ROOT / 'generated.json').read_text())
    assert len({item['id'] for item in entries}) == len(entries)
    assert {item['extension'] for item in entries} == set(config['required_extensions'])
    assert {str(p.relative_to(ROOT)) for p in (ROOT / 'samples').rglob('*') if p.is_file()} == {x['path'] for x in entries}
    for item in entries:
        item['validation'] = validate(item)
        item['documented_api'] = item['extension'] in OFFICIAL
        item['model_version'] = ('MinerU-HTML' if item['extension'] == 'html' else 'vlm') if item['documented_api'] else None
        item['suite'] = 'official_api' if item['documented_api'] else 'extra_text'
        item['smoke'] = SMOKE[item['extension']] == item['id']
        if 'repository' in item:
            item['source_url'] = f"https://raw.githubusercontent.com/{item['repository']}/{item['commit']}/{quote(item['source_path'])}"
        if args.ref:
            item['url'] = f"https://raw.githubusercontent.com/{args.repository}/{args.ref}/{quote(item['path'])}"
    assert sum(item['smoke'] for item in entries) == len(config['required_extensions'])
    stats = {'files': len(entries), 'extensions': dict(sorted(Counter(x['extension'] for x in entries).items())),
             'total_bytes': sum(x['validation']['bytes'] for x in entries), 'local_structure_validation': 'passed',
             'pipeline_execution': 'not_run', 'api_documentation_checked': '2026-11-04'}
    print(json.dumps(stats, ensure_ascii=False, indent=2))
    if not args.ref:
        return
    entries.sort(key=lambda x: (x['extension'], not x['smoke'], x['id']))
    write_json('manifest.json', {'schema_version': 1, 'sample_commit': args.ref, 'repository': args.repository,
                               'scope': config['scope'], 'stats': stats, 'samples': entries})
    fields = ['id', 'extension', 'suite', 'smoke', 'scenario', 'model_version', 'bytes', 'sha256', 'url', 'source_url', 'license']
    with (ROOT / 'manifest.csv').open('w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for item in entries:
            row = {key: item.get(key, '') for key in fields}
            row.update(bytes=item['validation']['bytes'], sha256=item['validation']['sha256'])
            writer.writerow(row)
    for filename, selected in [
        ('urls_smoke.txt', [x for x in entries if x['smoke']]),
        ('urls_official_api.txt', [x for x in entries if x['documented_api']]),
        ('urls_extra_text.txt', [x for x in entries if not x['documented_api']]),
    ]:
        (ROOT / filename).write_text(''.join(item['url'] + '\n' for item in selected))
    update_url_lists(ROOT)
    for model, name in [('vlm', 'vlm'), ('MinerU-HTML', 'html')]:
        selected = [x for x in entries if x['model_version'] == model]
        write_json(f'requests/{name}_batch.json', {'files': [{'url': x['url'], 'data_id': x['id']} for x in selected], 'model_version': model})
    lines = ['# 样本清单', '', '所有下载链接固定到样本 commit；⭐ 表示每种扩展名的首轮测试样本。', '',
             '| 格式 | 样本 | 测试场景 | 字节数 | API 分组 |', '|---|---|---|---:|---|']
    for item in entries:
        star = '⭐ ' if item['smoke'] else ''
        lines.append(f"| .{item['extension']} | {star}[{item['id']}]({item['url']}) | {item['scenario']} | {item['validation']['bytes']} | {item['suite']} |")
    (ROOT / 'CATALOG.md').write_text('\n'.join(lines) + '\n')


if __name__ == '__main__':
    main()

"""Build valid synthetic PDFs/BMPs that isolate page-count and byte-size limits."""
from hashlib import sha256
import io
import json
from pathlib import Path

from PIL import Image, ImageDraw
from pypdf import PdfReader, PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject, NumberObject
import pypdfium2 as pdfium
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen.canvas import Canvas

ROOT = Path(__file__).resolve().parents[1]
BOUNDARY = ROOT / 'boundary'
PAGE_SPECS = [('control_200_pages', 200), ('over_limit_201_pages', 201), ('over_limit_1000_pages', 1000)]


def text_pdf(target: str | io.BytesIO, pages: int, label: str, *, image_space: bool = False) -> None:
    canvas = Canvas(target, pagesize=A4, pageCompression=1, invariant=1)
    canvas.setTitle(label)
    canvas.setAuthor('mineru-pipeline-test-corpus contributors')
    width, height = A4
    for number in range(1, pages + 1):
        canvas.setFillColor(HexColor('#14304a'))
        canvas.setFont('Helvetica-Bold', 21)
        canvas.drawString(44, height - 65, 'Pipeline boundary test')
        canvas.setFont('Helvetica', 12)
        canvas.drawString(44, height - 90, label)
        canvas.setFont('Helvetica-Bold', 14)
        canvas.drawString(44, height - 126, f'PAGE {number:04d} OF {pages:04d}')
        canvas.setFont('Helvetica', 11)
        canvas.drawString(44, height - 149, f'SAMPLE-MARKER-{number:04d}')
        if image_space:
            canvas.drawString(44, height - 174, 'Visible uncompressed RGB chart; no trailing-byte padding.')
        else:
            canvas.drawString(44, height - 182, 'Synthetic content for page-count validation. No private data.')
            canvas.drawString(44, height - 204, 'Each page contains distinct searchable text and a small table.')
            rows = [('Item', 'Quantity', 'Amount'), ('Pencil', '3', '37.50'), ('Notebook', '2', '40.00'), ('Total', '5', '77.50')]
            for row, values in enumerate(rows):
                y = height - 260 - row * 32
                canvas.setFillColor(HexColor('#e9f0f5') if row == 0 else HexColor('#f7fafc'))
                canvas.rect(44, y - 12, width - 88, 30, stroke=0, fill=1)
                canvas.setFillColor(HexColor('#14304a'))
                for x, value in zip((55, 280, 410), values):
                    canvas.drawString(x, y, value)
        canvas.setFillColor(HexColor('#65788b'))
        canvas.setFont('Helvetica', 9)
        canvas.drawString(44, 35, 'MIT - original synthetic boundary fixture')
        canvas.drawRightString(width - 44, 35, f'{number} / {pages}')
        canvas.showPage()
    canvas.save()


def calibration_image(width: int, height: int, number: int) -> Image.Image:
    image = Image.new('RGB', (width, height), '#eff4f8')
    draw = ImageDraw.Draw(image)
    colors = ['#194567', '#3783ab', '#5ca398', '#d8aa51', '#ae6377', '#7e78aa']
    cell_w, cell_h = width // 6, height // 10
    for row in range(8):
        for col in range(6):
            left = col * cell_w + 10
            top = row * cell_h + height // 10
            draw.rectangle((left, top, left + cell_w - 20, top + cell_h - 20), fill=colors[(row + col + number) % len(colors)])
    draw.text((width // 30, height // 40), f'RGB CALIBRATION CHART - PAGE {number:02d}', fill='#14304a', font_size=max(30, width // 40))
    draw.text((width // 30, height * 93 // 100), 'SYNTHETIC SIZE-LIMIT TEST - NO PRIVATE DATA', fill='#14304a', font_size=max(25, width // 60))
    return image


def large_pdf(path: Path) -> None:
    source = io.BytesIO()
    text_pdf(source, 10, 'SIZE LIMIT ONLY - 10 PAGES - OVER 200 MiB', image_space=True)
    source.seek(0)
    writer = PdfWriter()
    writer.append(PdfReader(source))
    for number, page in enumerate(writer.pages, 1):
        image = calibration_image(2700, 2720, number)
        stream = DecodedStreamObject()
        stream.set_data(image.tobytes())
        image.close()
        stream.update({NameObject('/Type'): NameObject('/XObject'), NameObject('/Subtype'): NameObject('/Image'),
                       NameObject('/Width'): NumberObject(2700), NameObject('/Height'): NumberObject(2720),
                       NameObject('/ColorSpace'): NameObject('/DeviceRGB'), NameObject('/BitsPerComponent'): NumberObject(8)})
        resources = page['/Resources'].get_object()
        resources[NameObject('/XObject')] = DictionaryObject({NameObject('/Chart'): writer._add_object(stream)})
        content = DecodedStreamObject()
        content.set_data(page.get_contents().get_data() + b'\nq 495 0 0 498 50 75 cm /Chart Do Q\n')
        page[NameObject('/Contents')] = writer._add_object(content)
    writer.add_metadata({'/Title': 'Synthetic size-limit PDF with 10 uncompressed charts', '/Author': 'mineru-pipeline-test-corpus contributors'})
    with path.open('wb') as handle:
        writer.write(handle)
    writer.close()


def inspect(path: Path, expected_pages: int | None) -> dict:
    with path.open('rb') as stream:
        digest = sha256()
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    size = path.stat().st_size
    result = {'bytes': size, 'size_mb_decimal': round(size / 1_000_000, 6), 'size_mib': round(size / 2**20, 6), 'sha256': digest.hexdigest()}
    preview_dir = ROOT / 'scratch' / 'boundary'
    preview_dir.mkdir(parents=True, exist_ok=True)
    if path.suffix == '.pdf':
        reader = PdfReader(path, strict=True)
        assert len(reader.pages) == expected_pages
        document = pdfium.PdfDocument(path)
        assert len(document) == expected_pages
        for index in range(len(document)):
            page = document[index]
            textpage = page.get_textpage()
            text = textpage.get_text_range()
            assert f'SAMPLE-MARKER-{index + 1:04d}' in text, (path, index)
            textpage.close()
            if index in {0, len(document) // 2, len(document) - 1}:
                bitmap = page.render(scale=0.85)
                bitmap.to_pil().save(preview_dir / f'{path.stem}_{index + 1}.png')
                bitmap.close()
            page.close()
        document.close()
        result.update(pages=expected_pages, validation='pypdf strict + PDFium page count and per-page text; first/middle/last rendered')
    else:
        with Image.open(path) as image:
            assert image.format == 'BMP' and image.size == (9000, 8000)
            image.load()
            result.update(width=image.width, height=image.height, validation='Pillow full pixel decode')
            image.thumbnail((900, 800))
            image.save(preview_dir / f'{path.stem}.png')
    return result


def main() -> None:
    (BOUNDARY / 'files').mkdir(parents=True, exist_ok=True)
    (BOUNDARY / 'release_assets').mkdir(parents=True, exist_ok=True)
    entries = []
    specs = []
    for name, pages in PAGE_SPECS:
        path = BOUNDARY / 'files' / f'{name}.pdf'
        text_pdf(str(path), pages, f'PAGE COUNT TEST - {pages} PAGES')
        specs.append((name, path, pages, 'raw', 'page_count' if pages > 200 else 'control'))
    path = BOUNDARY / 'release_assets' / 'oversize_10_pages_rgb.pdf'
    large_pdf(path)
    specs.append(('oversize_10_pages_rgb', path, 10, 'release', 'file_size'))
    path = BOUNDARY / 'release_assets' / 'oversize_9000x8000_rgb.bmp'
    image = calibration_image(9000, 8000, 1)
    image.save(path, format='BMP')
    image.close()
    specs.append(('oversize_9000x8000_rgb', path, None, 'release', 'file_size'))
    for name, path, pages, hosting, scenario in specs:
        checked = inspect(path, pages)
        if scenario == 'file_size':
            assert checked['bytes'] > 200 * 2**20  # Exceeds both decimal MB and binary MiB interpretations.
        else:
            assert checked['bytes'] < 2_000_000
        entries.append({'id': name, 'path': str(path.relative_to(ROOT)), 'extension': path.suffix[1:],
                        'hosting': hosting, 'scenario': scenario, 'kind': 'synthetic', 'license': 'MIT',
                        'expected_boundary_behavior': 'passes_page_and_size_precheck' if scenario == 'control' else 'reject_if_documented_limit_is_enforced',
                        'actual_pipeline_result': 'not_run', **checked})
        print(name, checked['bytes'], 'bytes', pages, 'pages', flush=True)
    (BOUNDARY / 'inventory.json').write_text(json.dumps(entries, indent=2) + '\n')


if __name__ == '__main__':
    main()

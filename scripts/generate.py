"""Generate controlled text/HTML fixtures and document image format comparisons."""
import json
from pathlib import Path

from PIL import Image
import pypdfium2 as pdfium

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    source = json.loads((ROOT / 'sources.json').read_text())
    receipt = next(item for item in source['sources'] if item['id'] == 'markitdown_pdf_receipt')
    document = pdfium.PdfDocument(ROOT / receipt['path'])
    page = document[0]
    bitmap = page.render(scale=2.5)
    raster = bitmap.to_pil().convert('RGB').copy()
    bitmap.close()
    page.close()
    document.close()
    entries = []

    def record(path: str, scenario: str, *, derived: bool = False, text: list[str] | None = None) -> None:
        extension = Path(path).suffix[1:]
        item = {
            'id': Path(path).stem + ('_' + extension if Path(path).stem == 'synthetic_bilingual_report' else ''),
            'origin': 'derived-markitdown' if derived else 'original',
            'path': path,
            'extension': extension,
            'license': 'MIT',
            'scenario': scenario,
            'kind': 'derived' if derived else 'synthetic',
            'modification': scenario,
            'expected_text_contains': text or [],
            'expectation_note': 'Human-readable content anchors, not a complete accuracy ground truth.',
        }
        if derived:
            for key in ('repository', 'commit', 'source_path'):
                item[key] = receipt[key]
            item['derived_from'] = receipt['id']
            item['source_page'] = 1
        entries.append(item)

    def save_image(ext: str, suffix: str, image: Image.Image, image_format: str, scenario: str, **options) -> None:
        path = f'samples/{ext}/receipt_{suffix}.{ext}'
        (ROOT / path).parent.mkdir(parents=True, exist_ok=True)
        image.save(ROOT / path, format=image_format, **options)
        record(path, scenario, derived=True, text=['TECHMART ELECTRONICS', '821.14'])

    for ext, image_format in [('png', 'PNG'), ('jpg', 'JPEG'), ('jpeg', 'JPEG'), ('webp', 'WEBP'), ('gif', 'GIF'), ('bmp', 'BMP'), ('jp2', 'JPEG2000')]:
        options = {'quality': 95} if image_format in {'JPEG', 'WEBP'} else {}
        save_image(ext, f'baseline_{ext}', raster, image_format, 'same_receipt_document_format_comparison', **options)
    save_image('jpg', 'rotated_90', raster.rotate(90, expand=True), 'JPEG', 'ocr_document_rotated_90_degrees', quality=95)
    save_image('jpeg', 'low_quality', raster.resize((270, 990)), 'JPEG', 'ocr_low_resolution_lossy_compression', quality=25)
    transparent = raster.convert('RGBA')
    save_image('png', 'rgba', transparent, 'PNG', 'rgba_image_mode_opaque_alpha')

    html = '''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><title>Pipeline 样本报告</title>
<style>body{font:16px sans-serif;max-width:850px;margin:40px auto}table{border-collapse:collapse}th,td{border:1px solid #999;padding:8px}figure{margin:24px 0}</style></head>
<body><h1>Pipeline 样本报告 / Sample Report</h1><p>Sample ID: CORPUS-2026-001</p>
<p>这是一份合成的中英文测试文件，所有业务数据均为虚构。</p>
<h2>1. 销售表格 / Sales</h2><table><thead><tr><th>产品</th><th>数量</th><th>单价</th><th>金额</th></tr></thead>
<tbody><tr><td>测试铅笔 / Pencil</td><td>3</td><td>12.50</td><td>37.50</td></tr>
<tr><td>测试本 / Notebook</td><td>2</td><td>20.00</td><td>40.00</td></tr>
<tr><td colspan="3">合计 / Total</td><td>77.50</td></tr></tbody></table>
<h2>2. 公式 / Formula</h2><p>E = mc²</p><math xmlns="http://www.w3.org/1998/Math/MathML"><mrow><mi>a</mi><mo>+</mo><mi>b</mi><mo>=</mo><mi>c</mi></mrow></math>
<h2>3. 列表与链接</h2><ul><li>支持中文与 English</li><li>保留表格、标题和阅读顺序</li></ul><a href="#appendix">跳转附录</a>
<h2>4. 图形</h2><figure><svg xmlns="http://www.w3.org/2000/svg" width="300" height="100" role="img" aria-label="Sales chart"><rect x="10" y="10" width="140" height="25" fill="#247aab"/><rect x="10" y="50" width="200" height="25" fill="#3a9973"/><text x="220" y="70">77.50</text></svg><figcaption>图 1：合成数据柱状图</figcaption></figure>
<h2 id="appendix">附录 / Appendix</h2><pre>status = "ok"</pre><p>END-OF-SAMPLE</p></body></html>
'''
    text_samples = {
        'html': html,
        'md': '''# Pipeline 样本报告 / Sample Report

Sample ID: CORPUS-2026-001

这是一份合成的中英文测试文件，所有业务数据均为虚构。

## 销售表格

| 产品 | 数量 | 金额 |
| --- | ---: | ---: |
| 测试铅笔 / Pencil | 3 | 37.50 |
| 测试本 / Notebook | 2 | 40.00 |
| 合计 / Total | 5 | 77.50 |

## 数学公式

$E = mc^2$

- 中文与 English
- **加粗**、*斜体*、`inline code`

```python
status = "ok"
```

END-OF-SAMPLE
''',
        'txt': '''Pipeline 样本报告 / Sample Report
Sample ID: CORPUS-2026-001

这是一份合成的中英文测试文件，所有业务数据均为虚构。
产品\t数量\t金额
测试铅笔 / Pencil\t3\t37.50
测试本 / Notebook\t2\t40.00
合计 / Total\t5\t77.50

Formula: E = mc²
Unicode: 中文, café, αβγ
END-OF-SAMPLE
''',
        'rst': '''Pipeline 样本报告 / Sample Report
================================

Sample ID: CORPUS-2026-001

这是一份合成的中英文测试文件，所有业务数据均为虚构。

销售表格
--------

.. list-table:: Sales
   :header-rows: 1

   * - 产品
     - 数量
     - 金额
   * - 测试铅笔 / Pencil
     - 3
     - 37.50
   * - 测试本 / Notebook
     - 2
     - 40.00
   * - 合计 / Total
     - 5
     - 77.50

.. math::

   E = mc^2

.. code-block:: python

   status = "ok"

END-OF-SAMPLE
''',
        'tex': r'''\documentclass{article}
\usepackage[UTF8]{ctex}
\usepackage{amsmath}
\begin{document}
\section{Pipeline 样本报告 / Sample Report}
Sample ID: CORPUS-2026-001

这是一份合成的中英文测试文件，所有业务数据均为虚构。
\begin{tabular}{lrr}
产品 & 数量 & 金额 \\
测试铅笔 / Pencil & 3 & 37.50 \\
测试本 / Notebook & 2 & 40.00 \\
合计 / Total & 5 & 77.50 \\
\end{tabular}
\[ E = mc^2 \]
\begin{equation} \int_0^1 x^2\,dx = \frac{1}{3} \end{equation}
\begin{itemize}\item 中文与 English\item 测试列表\end{itemize}
END-OF-SAMPLE
\end{document}
''',
    }
    for ext, text in text_samples.items():
        path = f'samples/{ext}/synthetic_bilingual_report.{ext}'
        (ROOT / path).parent.mkdir(parents=True, exist_ok=True)
        (ROOT / path).write_text(text, encoding='utf-8')
        record(path, 'bilingual_headings_table_formula_list', text=['CORPUS-2026-001', '77.50', 'END-OF-SAMPLE'])
    # Encoding/newline cases intentionally preserve the same human-readable content.
    for name, content in [
        ('utf8_bom_crlf', ('\ufeff' + text_samples['txt'].replace('\n', '\r\n')).encode('utf-8')),
        ('gb18030', text_samples['txt'].encode('gb18030')),
    ]:
        path = f'samples/txt/synthetic_{name}.txt'
        (ROOT / path).write_bytes(content)
        record(path, f'text_encoding_{name}', text=['CORPUS-2026-001', '77.50', 'END-OF-SAMPLE'])
    (ROOT / 'generated.json').write_text(json.dumps(entries, ensure_ascii=False, indent=2) + '\n')
    print(f'Generated {len(entries)} samples; derived images share one source page.')


if __name__ == '__main__':
    main()

"""Publish URL metadata separately from the normal, within-limit sample suite."""
import argparse
import json
from pathlib import Path
import re
import subprocess

from update_url_lists import update_url_lists

ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = 'ShaoxinLi/mineru-pipeline-test-corpus'
TAG = 'boundary-v1'


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--ref', required=True)
    args = parser.parse_args()
    if not re.fullmatch('[0-9a-f]{40}', args.ref):
        parser.error('Use the full commit containing boundary/files')
    entries = json.loads((ROOT / 'boundary/inventory.json').read_text())
    for item in entries:
        if item['hosting'] == 'raw':
            assert subprocess.check_output(['git', 'show', f"{args.ref}:{item['path']}"], cwd=ROOT) == (ROOT / item['path']).read_bytes()
            item['url'] = f"https://raw.githubusercontent.com/{REPOSITORY}/{args.ref}/{item['path']}"
        else:
            item['url'] = f"https://github.com/{REPOSITORY}/releases/download/{TAG}/{Path(item['path']).name}"
        item['single_request'] = {'url': item['url'], 'data_id': item['id'], 'model_version': 'vlm'}
    metadata = {'schema_version': 1, 'sample_commit': args.ref, 'release_tag': TAG,
                'page_limit': 200, 'size_limit_documentation': '200 MB',
                'size_convention_note': 'Both large samples exceed 200,000,000 and 209,715,200 bytes.',
                'actual_pipeline_execution': 'not_run', 'samples': entries}
    (ROOT / 'boundary/manifest.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + '\n')
    (ROOT / 'boundary/urls.txt').write_text(''.join(x['url'] + '\n' for x in entries))
    update_url_lists(ROOT)
    (ROOT / 'boundary/requests.jsonl').write_text(''.join(json.dumps(x['single_request']) + '\n' for x in entries))
    checksums = ''.join(f"{x['sha256']}  {Path(x['path']).name}\n" for x in entries)
    (ROOT / 'boundary/SHA256SUMS').write_text(checksums)
    table = ['| 样本直链 | 页数 / 尺寸 | MB（十进制） | MiB（二进制） | 用途 |', '|---|---|---:|---:|---|']
    descriptions = {'control': '200 页对照', 'page_count': '仅超页', 'file_size': '仅超文件大小'}
    for x in entries:
        dimensions = str(x['pages']) + ' 页' if 'pages' in x else f"{x['width']} × {x['height']} 像素"
        table.append(f"| [{x['id']}]({x['url']}) | {dimensions} | {x['size_mb_decimal']:.6f} | {x['size_mib']:.6f} | {descriptions[x['scenario']]} |")
    intro = '''# 超页 / 超大边界测试集

新增 5 个原创合成样本：1 个正常阈值对照、2 个超页 PDF、2 个超 200 MB 的文件。
它们独立于基础 45 文件测试集，不会加入原有 smoke 列表或正常批量请求。

'''
    details = '''

## 使用

- [全部直链](urls.txt) / [机器可读 manifest](manifest.json) / [SHA-256](SHA256SUMS)
- [单文件请求体 JSONL](requests.jsonl)：每行是一个独立请求体，可用于兼容的 `/api/v4/extract/task`。建议一次测一个。
- [远程下载校验报告](verification.json)：记录 HTTP 状态、实际读取字节数与 SHA-256。

200 页 PDF 只应通过页数和大小预检查，不保证模型最终解析成功。
201 页和 1000 页样本用于观察服务是否拒绝、截断或继续处理超页文件；正常按官网上限实现时应拒绝。
10 页 PDF 的大小超过 200 MB/200 MiB，可独立测试文件大小限制。
BMP 同样超过这两种大小阈值，但它还具有 7200 万像素；如果服务先进行图像尺寸检查，可能先触发像素限制。
实际返回错误码和处理结果均须由你的 pipeline 验证，本仓库未运行内网解析接口。
不要指定局部页范围，否则会改变超页测试含义。

## 文件内容与验证

每个 PDF 页面都有独立页码、可检索的 `SAMPLE-MARKER-NNNN`，超页文件不是空白页堆叠。
大 PDF 含 10 个可见的未压缩 RGB 校准图，每个 2700 × 2720 像素；BMP 是真实的 24 位 RGB 校准图。
文件大小来自有效的图像像素数据，没有尾部填充、损坏容器或伪造扩展名。

所有 PDF 由 pypdf 严格模式和 PDFium 双重检查页数，并逐页检查文本标记。
各 PDF 的首页、中间页、末页已渲染检查；BMP 已完整像素解码。
提供 MB 与 MiB 两种计量，避免“200 MB”实现口径不一致。

## 托管与网络

三个小 PDF 使用固定 commit 的 `raw.githubusercontent.com` URL。
GitHub 普通仓库拒绝超过 100 MiB 的文件，因此两个超大文件使用公开 Release 附件，无需登录。
Release 下载链接会从 `github.com` 跳转到 `release-assets.githubusercontent.com`。
提供的是稳定的 Release 入口 URL，不是临时签名下载 URL；`boundary-v1` 的附件不会覆盖更新。
公司内网是否允许 Release 下载仍待验证。若受限，可下载附件后放入内网对象存储并替换 manifest 中的 URL。

GitHub 限制依据：[大文件限制](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github)、[Release 附件](https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases)。

## 复现

```bash
uv pip install --python .venv/bin/python -r requirements-boundary.txt
.venv/bin/python scripts/build_boundary_samples.py
# 提交 boundary/files 后，使用该真实 commit 生成 URL 清单：
.venv/bin/python scripts/catalog_boundary.py --ref COMMIT_SHA
# 流式下载、计算哈希，默认不会另存 400 多 MB 的副本：
python3 scripts/verify_boundary_urls.py
```

大文件保存在本地 `boundary/release_assets/`，已被 Git 忽略，只作为 Release 附件上传。
原创内容采用仓库根 MIT 许可。
'''
    (ROOT / 'boundary/README.md').write_text(intro + '\n'.join(table) + details)
    (ROOT / 'boundary/RELEASE_NOTES.md').write_text('Boundary test fixtures: 200/201/1000-page PDFs and >200 MB PDF/BMP.\n\n' + '\n'.join(table) + '\n\nAll original synthetic content, MIT licensed. Large files contain valid uncompressed image data. SHA-256 values are in the attached SHA256SUMS. No pipeline execution has been performed. See boundary/README.md for usage and network requirements.\n')


if __name__ == '__main__':
    main()

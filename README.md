# MinerU pipeline URL 测试集

共 50 个样本，19 种扩展名：45 个基础样本（约 7.83 MB）和 5 个边界样本。用于通过文件 URL 拉取输入的文档解析 pipeline。
样本包括公开项目测试文件、其明确标注的图片转换版本、本仓库合成文件，以及用户提供的 GHAttack 论文。

另有 [5 个超页 / 超大边界样本](boundary/README.md)：200 页对照、201 页、1000 页 PDF，以及超过 200 MB 的 PDF 和 BMP。

## 使用入口

- [完整样本目录](CATALOG.md)：逐个文件的下载直链及场景。
- [manifest.json](manifest.json)：机器可读清单，包含 URL、大小、SHA-256、来源 commit、许可、格式和测试分组。
- [manifest.csv](manifest.csv)：便于表格工具查看的清单。
- [urls_smoke.txt](urls_smoke.txt)：每种扩展名一个，共 19 个，适合第一轮连通性和格式测试。
- **[urls.txt](urls.txt)：全部 50 个文件的 URL 汇总，一行一个；前 45 个为基础样本，最后 5 个为边界样本。**
- [urls_regular.txt](urls_regular.txt)：原来的 45 个基础样本直链。
- [urls_official_api.txt](urls_official_api.txt)：官网明确列出的格式，共 39 个文件。
- [urls_extra_text.txt](urls_extra_text.txt)：额外文本格式，共 6 个文件。

普通样本 URL 使用完整 Git commit 固定文件内容；两个超大文件使用 `boundary-v1` Release 附件直链。全部样本均不使用 Git LFS。
仓库为公开仓库，下载无需 GitHub 登录或 token。

## 范围

按 [MinerU 精准解析 API 文档](https://mineru.net/apiManage/docs)于 2026-11-04 明确列出的格式整理，
并加上用户要求的四种文本格式。此处不是对 MinerU 所有版本或所有产品入口的支持声明。

| 分组 | 扩展名 | 文件数 | 路由建议 |
|---|---|---:|---|
| PDF | `.pdf` | 8 | `vlm` 或 `pipeline` |
| 图片 | `.png` `.jpg` `.jpeg` `.jp2` `.webp` `.gif` `.bmp` | 13 | `vlm` 或 `pipeline` |
| Word | `.doc` `.docx` | 7 | `vlm` 或 `pipeline` |
| PowerPoint | `.ppt` `.pptx` | 5 | `vlm` 或 `pipeline` |
| Excel | `.xls` `.xlsx` | 5 | `vlm` 或 `pipeline` |
| HTML | `.html` | 1 | `MinerU-HTML` |
| 额外文本 | `.md` `.txt` `.rst` `.tex` | 6 | 自建 pipeline 的文本路径；官网未明确列出 |

不含 `.tiff`、`.rtf`、`.odt`、`.ods`、`.odp`、`.epub`、`.ofd`、`.htm`、`.shtml`、`.mhtml`、`.mht`、`.csv`、`.tsv` 输入样本。
根目录的 CSV、JSON、Markdown、TXT 是清单或说明文件，不应作为样本目录递归输入。

## 覆盖的场景

- PDF：原生文本、纯扫描件（无文本层）、小票、多页维修单、跨页无边框表格、编号列表、订单排版。
- Word：旧版二进制格式、图片、编号列表、现代 OOXML、OMML 公式、批注、相对链接。
- PowerPoint：旧版与现代格式、图片、组合形状、SVG 图片。
- Excel：旧版与现代格式、图表、日期格式、超链接。
- 图片：同一小票的七种图片编码、90 度旋转、低分辨率有损压缩、RGBA 模式，另有上游独立图片。
- HTML：自包含中英文标题、表格、合并单元格、公式、内联 SVG、列表、锚点和代码。无需外部资源或 JavaScript。
- 文本：中英文内容、表格或表格语法、公式、代码；TXT 额外提供 UTF-8 BOM + CRLF、GB18030 编码。

10 个 `receipt_*` 图片是同一 PDF 首页的派生文件，用于控制变量比较格式，不代表 10 份独立业务文档。
扫描报告含局部重叠文字，是较难的上游样本。照片、图形类样本不保证含有大量可 OCR 的正文。
`expected_text_contains` 只给部分受控样本提供内容检查点，不是完整的人工标注答案。
本集适合格式覆盖和回归测试，尚不覆盖所有业务场景、超大文件、加密文件或损坏文件的错误处理。

## API 请求示例

[requests/vlm_batch.json](requests/vlm_batch.json) 包含 38 个非 HTML 官网格式样本；
[requests/html_batch.json](requests/html_batch.json) 包含 1 个 HTML 样本。
这两个文件是标准 JSON 请求体，可用于官网的 URL 批量提交接口，或映射到兼容的自建接口。
四种额外文本格式不会混入这两个请求体。

```bash
# 将 BASE_URL 指向自己的兼容服务；TOKEN 从本地环境提供。
curl --fail-with-body -X POST "${BASE_URL}/api/v4/extract/task/batch" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H 'Content-Type: application/json' \
  --data-binary @requests/vlm_batch.json

curl --fail-with-body -X POST "${BASE_URL}/api/v4/extract/task/batch" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H 'Content-Type: application/json' \
  --data-binary @requests/html_batch.json
```

提交响应只代表任务创建成功。批量结果需要通过兼容接口的 `/api/v4/extract-results/batch/{batch_id}` 查询，
最终按文件检查成功/失败状态、输出和内容检查点。
官网自身的 GitHub URL 下载网络限制与公司自建服务不同；目标下载进程的网络可达性应在内网验证。
Raw 返回的 HTTP Content-Type 不一定是格式专用 MIME；建议保留 URL 扩展名并结合文件内容识别类型。

## 验证与复现

本地检查包括：完整扩展名覆盖、文件非空、真实格式签名、ZIP CRC、OOXML 主文档 XML、OLE 文档流、
全部图片解码、PDF 打开和页数、文本编码解码、受控文本检查点。上游下载还按 Git blob SHA 校验原始字节。
这些检查不等同于解析精度验证。

[verification/remote.json](verification/remote.json) 记录匿名 GET 下载的 HTTP 状态、字节数与 SHA-256 校验结果。
当前基础样本验证结果：**45/45 通过**。
该报告来自运行校验脚本的机器，不代表已经在公司内网运行；尚未调用用户的解析 pipeline。

仅检查内网下载时，`verify_urls.py` 只依赖 Python 标准库：

```bash
python3 scripts/verify_urls.py --smoke --output verification/intranet-smoke.json
python3 scripts/verify_urls.py --output verification/intranet-all.json
```

重新收集和生成需要这些依赖：

```bash
uv venv .venv
uv pip install --python .venv/bin/python -r requirements.txt
.venv/bin/python scripts/collect.py
.venv/bin/python scripts/generate.py
.venv/bin/python scripts/catalog.py  # 仅检查本地文件
# 使用包含最终样本的真实 commit；提交样本后才生成目录，避免自引用 commit。
.venv/bin/python scripts/catalog.py --ref COMMIT_SHA
```

固定下载的原始文件可按上游 SHA 完全复现；图片渲染可能受平台和底层库影响，正式回归以已发布的样本 SHA-256 为准。

## 来源与许可

27 个原始文件来自 Microsoft MarkItDown 和 Apache Tika 的测试目录，另有 1 个用户提供的 GHAttack 论文 PDF，均保留原始字节。
10 个图片是 MarkItDown 小票 PDF 的转换版本；7 个中英文网页/文本文件由本仓库合成。
详见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)、[licenses](licenses) 和每条 manifest 的来源信息。
本仓库原创脚本及合成内容使用 MIT；第三方文件保留其上游许可与版权声明，不因仓库根 LICENSE 而重新许可。

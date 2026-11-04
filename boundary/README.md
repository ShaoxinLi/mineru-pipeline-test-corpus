# 超页 / 超大边界测试集

新增 5 个原创合成样本：1 个正常阈值对照、2 个超页 PDF、2 个超 200 MB 的文件。
它们独立于基础 45 文件测试集，不会加入原有 smoke 列表或正常批量请求。

| 样本直链 | 页数 / 尺寸 | MB（十进制） | MiB（二进制） | 用途 |
|---|---|---:|---:|---|
| [control_200_pages](https://raw.githubusercontent.com/ShaoxinLi/mineru-pipeline-test-corpus/430af52d4f6dd02a09ca1cd192bdc6767c01cd02/boundary/files/control_200_pages.pdf) | 200 页 | 0.206729 | 0.197152 | 200 页对照 |
| [over_limit_201_pages](https://raw.githubusercontent.com/ShaoxinLi/mineru-pipeline-test-corpus/430af52d4f6dd02a09ca1cd192bdc6767c01cd02/boundary/files/over_limit_201_pages.pdf) | 201 页 | 0.207761 | 0.198136 | 仅超页 |
| [over_limit_1000_pages](https://raw.githubusercontent.com/ShaoxinLi/mineru-pipeline-test-corpus/430af52d4f6dd02a09ca1cd192bdc6767c01cd02/boundary/files/over_limit_1000_pages.pdf) | 1000 页 | 1.030535 | 0.982795 | 仅超页 |
| [oversize_10_pages_rgb](https://github.com/ShaoxinLi/mineru-pipeline-test-corpus/releases/download/boundary-v1/oversize_10_pages_rgb.pdf) | 10 页 | 220.338466 | 210.131136 | 仅超文件大小 |
| [oversize_9000x8000_rgb](https://github.com/ShaoxinLi/mineru-pipeline-test-corpus/releases/download/boundary-v1/oversize_9000x8000_rgb.bmp) | 9000 × 8000 像素 | 216.000054 | 205.993704 | 仅超文件大小 |

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

远程匿名下载验证：**5/5 通过**，包括两个大文件的完整字节数和 SHA-256 校验。校验来自本机，尚未运行公司内网 pipeline。

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

Boundary test fixtures: 200/201/1000-page PDFs and >200 MB PDF/BMP.

| 样本直链 | 页数 / 尺寸 | MB（十进制） | MiB（二进制） | 用途 |
|---|---|---:|---:|---|
| [control_200_pages](https://raw.githubusercontent.com/ShaoxinLi/mineru-pipeline-test-corpus/430af52d4f6dd02a09ca1cd192bdc6767c01cd02/boundary/files/control_200_pages.pdf) | 200 页 | 0.206729 | 0.197152 | 200 页对照 |
| [over_limit_201_pages](https://raw.githubusercontent.com/ShaoxinLi/mineru-pipeline-test-corpus/430af52d4f6dd02a09ca1cd192bdc6767c01cd02/boundary/files/over_limit_201_pages.pdf) | 201 页 | 0.207761 | 0.198136 | 仅超页 |
| [over_limit_1000_pages](https://raw.githubusercontent.com/ShaoxinLi/mineru-pipeline-test-corpus/430af52d4f6dd02a09ca1cd192bdc6767c01cd02/boundary/files/over_limit_1000_pages.pdf) | 1000 页 | 1.030535 | 0.982795 | 仅超页 |
| [oversize_10_pages_rgb](https://github.com/ShaoxinLi/mineru-pipeline-test-corpus/releases/download/boundary-v1/oversize_10_pages_rgb.pdf) | 10 页 | 220.338466 | 210.131136 | 仅超文件大小 |
| [oversize_9000x8000_rgb](https://github.com/ShaoxinLi/mineru-pipeline-test-corpus/releases/download/boundary-v1/oversize_9000x8000_rgb.bmp) | 9000 × 8000 像素 | 216.000054 | 205.993704 | 仅超文件大小 |

All original synthetic content, MIT licensed. Large files contain valid uncompressed image data. SHA-256 values are in the attached SHA256SUMS. No pipeline execution has been performed. See boundary/README.md for usage and network requirements.

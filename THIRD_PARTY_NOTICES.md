# Third-party sources and modifications

## Microsoft MarkItDown

- Repository: https://github.com/microsoft/markitdown
- Pinned commit: `7482c092d9c0074a89803c9fdb63a969e7fe17fc`
- Source directory: `packages/markitdown/tests/test_files/`
- Repository license: MIT. Full upstream text: [licenses/markitdown/LICENSE](licenses/markitdown/LICENSE).
- Copyright (c) Microsoft Corporation.
- Files prefixed `markitdown_` retain the original bytes. Renaming is only for local namespace clarity.
- Files prefixed `receipt_` are modified versions: first page of `RECEIPT-2024-TXN-98765_retail_purchase.pdf` rendered with PDFium, then encoded with Pillow. Specific rotation, resizing, compression and image-mode changes are recorded in the manifest. These files retain the upstream MIT attribution.

## Apache Tika

- Repository: https://github.com/apache/tika
- Pinned commit: `48010f83ad3869119f54546cbb272fde88130283`
- Source directories: test resources in the Microsoft and image parser modules; exact paths in `sources.json`.
- Repository license: Apache-2.0, including the upstream component license notices. Full upstream text: [licenses/tika/LICENSE.txt](licenses/tika/LICENSE.txt).
- Upstream attribution: [licenses/tika/NOTICE.txt](licenses/tika/NOTICE.txt).
- Files prefixed `tika_` retain the original bytes. Only the local filename changes.

License labels record the selected upstream revision's repository license; preserve any copyright or license notices embedded in individual documents as well. This collection does not claim ownership of third-party content or endorsement by upstream projects.

## Original content

The `synthetic_*` HTML and text samples contain fictional values and were authored for this test corpus. Original scripts and synthetic samples are provided under the root MIT license.

## User-provided GHAttack paper

- File: `samples/pdf/ghattack.pdf`
- Original filename: `GHAttack - Generative adversarial attacks on heterogeneous graph neural networks.pdf`
- Uploaded unchanged at the user's explicit request.
- License identifier: `NOASSERTION`; no additional reuse license is asserted. Original copyright and embedded notices remain applicable. The repository MIT license does not relicense this paper.

# Parser Adapters

Parser adapters convert local source files into CTL packages.

They may:

- read local documents, PDFs, HTML, text, JSON, images, and archives
- extract text, tables, figures, captions, metadata, and visual crops
- write CTL records, assets, manifests, semantic HTML, search indexes, and OKF cards

They must not:

- connect to databases
- call social platforms
- sync cloud storage
- post messages
- manage agents or workflow jobs
- read credentials except documented parser-specific config
- mutate external systems

## Built-In MVP Parser Adapters

| Adapter | Status | Dependency | Best For |
| --- | --- | --- | --- |
| `parser.fileinfo` | working | Python standard library | source metadata, checksums, provenance starter records |
| `parser.basic_html` | working | Python standard library | simple/generated HTML, links, images, semantic blocks |
| `parser.basic_json` | working | Python standard library | JSON metadata, API exports, structured manifests |
| `parser.basic_text` | working | Python standard library | txt, markdown, csv, tsv, plain notes |
| `parser.basic_pdf` | working when installed | optional `pdfplumber` or `pypdf` | born-digital PDFs, simple tables, simple figures |
| `parser.codebase` | working | Python standard library plus optional Git metadata | source trees, README files, code docs, repo notes, simple code graphs |

## Planned Optional Parser Bridges

These stay optional. Users install the external tools themselves; CTL adapters
only translate their outputs into CTL packages.

| Adapter | Status | External Tool | Best For |
| --- | --- | --- | --- |
| `parser.docling` | prototype private | Docling | PDF/DOCX layout, tables, figures |
| `parser.mineru` | prototype private | MinerU | academic/scientific PDFs, formulas, complex layouts |
| `parser.paddleocr` | prototype private | PaddleOCR | OCR, screenshots, scanned pages, text inside images |
| `parser.pandoc` | planned | Pandoc CLI | legacy format conversion and document bridges |
| `parser.playwright` | planned | Playwright | rendered websites and JavaScript-heavy pages |

Parser bridges should not own databases, cloud sync, social intake, or agent
workflow state. They read a source and produce a CTL package.

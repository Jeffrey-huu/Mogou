"""Convert every local Docling fixture without exposing its contents in Git."""

from __future__ import annotations

import json
import os
import shutil
import sys
from collections import Counter
from pathlib import Path

TEST_ROOT = Path(__file__).parent
INPUT_DIR = TEST_ROOT / "inputs"
OUTPUT_DIR = TEST_ROOT / "outputs"
REPORT_PATH = OUTPUT_DIR / "batch-report.json"
NON_DOCUMENT_SUFFIXES = {".py"}

# Keep every model cache local to this private test suite.
PRIVATE_CACHE = TEST_ROOT / ".cache"
PRIVATE_HOME = PRIVATE_CACHE / "home"
os.environ.setdefault("DOCLING_CACHE_DIR", str(PRIVATE_CACHE / "docling"))
os.environ.setdefault("HF_HOME", str(PRIVATE_CACHE / "huggingface"))
os.environ.setdefault("XDG_CACHE_HOME", str(PRIVATE_CACHE / "xdg"))
os.environ.setdefault("HOME", str(PRIVATE_HOME))
os.environ.setdefault("USERPROFILE", str(PRIVATE_HOME))

# Docling delegates legacy .xls conversion to LibreOffice on Windows.
libreoffice_dir = Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "LibreOffice" / "program"
if (libreoffice_dir / "soffice.exe").exists() and not shutil.which("soffice"):
    os.environ["PATH"] = f"{libreoffice_dir}{os.pathsep}{os.environ['PATH']}"

from docling.datamodel.base_models import ConversionStatus
from docling.document_converter import DocumentConverter


def output_path_for(source: Path) -> Path:
    relative = source.relative_to(INPUT_DIR)
    # Preserve the original suffix to avoid collisions such as report.pdf/report.docx.
    return OUTPUT_DIR / relative.with_suffix(f"{relative.suffix}.md")


def main() -> int:
    sources = sorted(path for path in INPUT_DIR.rglob("*") if path.is_file())
    if not sources:
        print(f"No files found in {INPUT_DIR}")
        return 0

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    converter = DocumentConverter()
    records: list[dict[str, str]] = []

    for source in sources:
        relative = source.relative_to(INPUT_DIR)
        if source.suffix.lower() in NON_DOCUMENT_SUFFIXES:
            records.append({"path": str(relative), "status": "skipped"})
            continue

        try:
            result = converter.convert(source, raises_on_error=False)
            if result.status != ConversionStatus.SUCCESS:
                records.append(
                    {
                        "path": str(relative),
                        "status": "failed",
                        "detail": "; ".join(str(error) for error in result.errors)
                        or result.status.value,
                    }
                )
                continue

            destination = output_path_for(source)
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(
                result.document.export_to_markdown(), encoding="utf-8"
            )
            records.append({"path": str(relative), "status": "passed"})
        except Exception as error:  # Keep the suite running after one bad fixture.
            records.append(
                {
                    "path": str(relative),
                    "status": "failed",
                    "detail": f"{type(error).__name__}: {error}",
                }
            )

    REPORT_PATH.write_text(
        json.dumps({"results": records}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    totals = Counter(record["status"] for record in records)
    print(
        "Docling batch test: "
        f"{totals['passed']} passed, {totals['failed']} failed, "
        f"{totals['skipped']} skipped."
    )
    return 1 if totals["failed"] else 0


if __name__ == "__main__":
    sys.exit(main())

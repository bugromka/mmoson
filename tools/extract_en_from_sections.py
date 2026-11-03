#!/usr/bin/env python3
"""Compatibility entry point for building the Edition 8 English DOCX.

Use tools/combine_sections.py --language both to build both language files.
"""
from combine_sections import main


if __name__ == "__main__":
    raise SystemExit(main(default_language="en"))

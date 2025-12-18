"""document_processing package

Note: Avoid importing submodules at package import time to prevent heavy dependency
errors (e.g. pypdf) if those packages are missing. Import submodules explicitly.
"""
__all__ = ["TextCleaner", "OptimalChunker", "PDFLoader", "WebScraperLoader"]

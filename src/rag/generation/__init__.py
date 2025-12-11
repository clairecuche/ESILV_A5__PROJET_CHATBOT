"""generation package for RAG components

Avoid importing submodules at package import time. Import needed submodules explicitly
where necessary to prevent heavy imports during module discovery.
"""
__all__ = ["IndexingPipeline", "Retriever", "OllamaLLM", "RAGPipeline"]

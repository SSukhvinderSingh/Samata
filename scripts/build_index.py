"""
Script to build / refresh the Samata RAG FAISS & BM25 Index from data/corpus/ directory.
Run this script to index statutes, case laws, and synthetic templates.
"""

import sys
import os
from pathlib import Path

# Add project root to sys.path
sys.path.append(str(Path(__file__).parent.parent))

from skills.rag_pipeline import load_or_build_index

def main():
    print("=" * 60)
    print("  Samata RAG Index Builder")
    print("=" * 60)
    print("Scanning data/corpus/ directory for legal documents...")
    
    res = load_or_build_index(force_rebuild=True)
    print(f"Index build status: {res['status']}")
    print(f"Total chunks indexed: {res['chunk_count']}")
    print("Indexing complete! Index ready for Samata retrieval.")

if __name__ == "__main__":
    main()

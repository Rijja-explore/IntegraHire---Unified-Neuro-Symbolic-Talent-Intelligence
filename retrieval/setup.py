#!/usr/bin/env python3
"""
Setup and initialization script for the retrieval subsystem.

Run this to:
1. Verify dependencies are installed
2. Check configuration
3. Build indexes (optional)
"""

import sys
from pathlib import Path

def check_dependencies():
    """Check if all required dependencies are installed."""
    print("Checking dependencies...")
    dependencies = {
        "sentence_transformers": "sentence-transformers",
        "rank_bm25": "rank-bm25",
        "faiss": "faiss-cpu",
        "numpy": "numpy",
        "pandas": "pandas",
        "pydantic": "pydantic",
    }
    
    missing = []
    for module, package in dependencies.items():
        try:
            __import__(module)
            print(f"  ✓ {package}")
        except ImportError:
            missing.append(package)
            print(f"  ✗ {package} (MISSING)")
    
    if missing:
        print(f"\nMissing dependencies: {', '.join(missing)}")
        print(f"\nInstall with:")
        print(f"  pip install -r retrieval/requirements.txt")
        return False
    
    print("  ✓ All dependencies installed\n")
    return True


def check_configuration():
    """Check system configuration."""
    print("Checking configuration...")
    try:
        from retrieval.config import get_config
        config = get_config()
        
        print(f"  ✓ Embedding model: {config.embedding.model_name}")
        print(f"  ✓ Embedding dimension: (will determine after first load)")
        print(f"  ✓ BM25 k1: {config.bm25.k1}")
        print(f"  ✓ RRF k: {config.retrieval.rrf_k}")
        print(f"  ✓ Weights: BM25={config.retrieval.bm25_weight}, Embedding={config.retrieval.embedding_weight}")
        print("  ✓ Configuration loaded\n")
        return True
    except Exception as e:
        print(f"  ✗ Configuration error: {e}\n")
        return False


def check_data_file():
    """Check if candidates.jsonl exists."""
    print("Checking data files...")
    candidates_file = Path(__file__).parent.parent / "candidates.jsonl"
    
    if candidates_file.exists():
        print(f"  ✓ Found candidates.jsonl ({candidates_file.stat().st_size / 1024 / 1024:.1f} MB)\n")
        return True
    else:
        print(f"  ✗ candidates.jsonl not found at {candidates_file}")
        print("    Place candidates.jsonl in the project root directory\n")
        return False


def build_indexes_prompt():
    """Prompt user to build indexes."""
    print("Would you like to build indexes now? (y/n): ", end="")
    response = input().strip().lower()
    
    if response == 'y':
        build_indexes()
    else:
        print("You can build indexes later by running:")
        print("  from retrieval import RetrievalEngine")
        print("  engine = RetrievalEngine()")
        print("  engine.build_indexes(Path('candidates.jsonl'))")


def build_indexes():
    """Build indexes from candidates file."""
    print("\nBuilding indexes...")
    try:
        from retrieval import RetrievalEngine
        from pathlib import Path
        import time
        
        candidates_file = Path(__file__).parent.parent / "candidates.jsonl"
        index_dir = Path(__file__).parent.parent / "retrieval_indices"
        
        engine = RetrievalEngine(index_dir=index_dir)
        
        start_time = time.time()
        stats = engine.build_indexes(candidates_file)
        elapsed = time.time() - start_time
        
        print(f"\n✓ Index building completed in {elapsed:.1f}s")
        print(f"  - Candidates: {stats['total_candidates']}")
        print(f"  - Embeddings: {stats['embeddings_shape']}")
        print(f"  - Index directory: {index_dir}\n")
        return True
        
    except Exception as e:
        print(f"\n✗ Error building indexes: {e}\n")
        return False


def main():
    """Run setup checks."""
    print("=" * 70)
    print("RETRIEVAL SUBSYSTEM - SETUP & VERIFICATION")
    print("=" * 70)
    print()
    
    checks = [
        ("Dependencies", check_dependencies),
        ("Configuration", check_configuration),
        ("Data Files", check_data_file),
    ]
    
    results = {}
    for name, check_func in checks:
        try:
            results[name] = check_func()
        except Exception as e:
            print(f"✗ {name} check failed: {e}\n")
            results[name] = False
    
    # Summary
    print("=" * 70)
    print("SETUP SUMMARY")
    print("=" * 70)
    
    all_passed = all(results.values())
    
    if all_passed:
        print("✓ All checks passed!\n")
        print("Next steps:")
        print("1. Verify candidates.jsonl is in the project root")
        print("2. Build indexes (optional, can be done programmatically)")
        print("3. Try running an example:")
        print("   python -m retrieval.examples.demo")
        print("   python -m retrieval.examples.quickstart\n")
        
        # Prompt to build indexes
        if check_data_file():
            build_indexes_prompt()
        
    else:
        print("✗ Some checks failed. Please fix the issues above.\n")
        sys.exit(1)


if __name__ == "__main__":
    main()

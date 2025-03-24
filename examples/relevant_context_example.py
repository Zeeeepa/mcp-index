"""
Example script demonstrating the RelevantCodeContextRetriever
"""

import os
import sys
import json
from pathlib import Path

# Add parent directory to path to import mcp_code_indexer
sys.path.append(str(Path(__file__).parent.parent))

from mcp_code_indexer.config import Config
from mcp_code_indexer.relevant_context_retriever import RelevantCodeContextRetriever

def main():
    """Main function"""
    # Create config
    config = Config({
        "storage": {
            "vector_db_path": "./vector_db",
            "cache_dir": "./cache"
        },
        "indexer": {
            "embedding_model": "all-MiniLM-L6-v2",
            "batch_size": 32,
            "optimization_options": {
                "use_ast_cache": True,
                "normalize_level": "NORMAL",
                "compress_threshold": 1000,
                "cache_context": True,
                "parallel_processing": True
            }
        },
        "agents": {
            "enabled": True
        }
    })
    
    # Create retriever
    retriever = RelevantCodeContextRetriever(config)
    
    # Check if project path is provided
    if len(sys.argv) < 2:
        print("Usage: python relevant_context_example.py <project_path> [query]")
        return
    
    project_path = sys.argv[1]
    
    # Index project if not already indexed
    print(f"Indexing project: {project_path}")
    project_id = retriever.index_project(project_path, progress_callback=print_progress)
    
    # Wait for indexing to complete
    import time
    while True:
        status, progress = retriever.get_indexing_status(project_id)
        if status == "completed":
            print(f"Indexing completed: {progress:.2f}")
            break
        elif status == "failed":
            print(f"Indexing failed: {progress:.2f}")
            return
        else:
            print(f"Indexing in progress: {progress:.2f}")
            time.sleep(1)
    
    # Get query from command line or use default
    query = sys.argv[2] if len(sys.argv) > 2 else "search functionality"
    
    # Get current file for context (using this file as an example)
    current_file = __file__
    current_line = 50  # Line number in this file
    
    # Get relevant context
    print(f"Searching for: {query}")
    print(f"Current context: {current_file}:{current_line}")
    
    results = retriever.get_relevant_context(
        query=query,
        current_file=current_file,
        current_line=current_line,
        limit=5
    )
    
    # Print results
    print("\nResults:")
    print(json.dumps(results, indent=2, default=str))
    
    # Print top result with enhanced context
    if results["results"]:
        top_result = results["results"][0]
        print("\nTop Result:")
        print(f"File: {top_result.get('file_path')}")
        print(f"Lines: {top_result.get('start_line')}-{top_result.get('end_line')}")
        print(f"Similarity: {top_result.get('similarity', 0):.4f}")
        
        if "enhanced_context" in top_result:
            enhanced = top_result["enhanced_context"]
            print(f"\nEnhanced Context ({enhanced.get('type', 'unknown')}):")
            if enhanced.get('name'):
                print(f"Name: {enhanced.get('name')}")
            if enhanced.get('dependencies'):
                print(f"Dependencies: {enhanced.get('dependencies')}")
            print("\nContent:")
            print("```")
            print(enhanced.get('content', ''))
            print("```")

def print_progress(status, progress):
    """Print indexing progress"""
    print(f"Indexing status: {status}, progress: {progress:.2f}")

if __name__ == "__main__":
    main()
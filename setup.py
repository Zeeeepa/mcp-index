#!/usr/bin/env python
from setuptools import setup, find_packages
import os
import subprocess
from pathlib import Path

# Get long description from README.md
with open("README.md", encoding="utf-8") as f:
    long_description = f.read()

# Get version from mcp_code_indexer/__init__.py
about = {}
with open("mcp_code_indexer/__init__.py", encoding="utf-8") as f:
    exec(f.read(), about)

# Define parser language libraries to download
LANGUAGES = ["python", "javascript", "typescript", "php", "rust", "java", "go", "c", "cpp"]

# Function to download and build tree-sitter language libraries
def download_tree_sitter_languages():
    try:
        from tree_sitter import Language
        
        parsers_dir = Path("mcp_code_indexer") / "parsers"
        parsers_dir.mkdir(exist_ok=True)
        
        # Clone repositories and build languages
        for lang in LANGUAGES:
            print(f"Setting up tree-sitter-{lang}...")
            repo_name = f"tree-sitter-{lang}"
            repo_url = f"https://github.com/tree-sitter/{repo_name}.git"
            
            # Skip if already exists
            if (parsers_dir / f"{lang}.so").exists() or (parsers_dir / f"{lang}.dll").exists():
                print(f"  - {lang} parser already exists, skipping")
                continue
                
            # Clone repository to temporary directory
            temp_dir = Path("temp_parsers") / repo_name
            temp_dir.parent.mkdir(exist_ok=True)
            
            if not temp_dir.exists():
                subprocess.check_call(["git", "clone", "--depth", "1", repo_url, str(temp_dir)])
                
            # Build the language
            try:
                Language.build_library(
                    str(parsers_dir / f"{lang}"),
                    [str(temp_dir)]
                )
                print(f"  - {lang} parser built successfully")
            except Exception as e:
                print(f"  - Error building {lang} parser: {e}")
                
    except ImportError:
        print("tree-sitter not installed, skipping language download")
    except Exception as e:
        print(f"Failed to download tree-sitter languages: {e}")

# Define package dependencies
requirements = [
    "flask>=2.0.0",
    "numpy>=1.20.0",
    "chromadb>=0.4.18",
    "sentence-transformers>=2.2.2",
    "tree-sitter>=0.20.1",
    "pyyaml>=6.0",
    "requests>=2.28.0",
]

# Optional dependencies
extras_require = {
    "llm": [
        "langchain>=0.0.267",
        "langchain-huggingface>=0.0.6",
        "langchain-chroma>=0.0.1",
        "openai>=1.3.0",
        "transformers>=4.36.0",
    ],
    "dev": [
        "pytest>=7.0.0",
        "black>=23.1.0",
        "isort>=5.12.0",
        "flake8>=6.0.0",
    ]
}

# Download tree-sitter language libraries
download_tree_sitter_languages()

setup(
    name="mcp-code-indexer",
    version=about["__version__"],
    description="An AI-powered code indexing and search tool for large codebases",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author=about["__author__"],
    author_email="info@mcpprotocol.org",
    url="https://github.com/mcpprotocol/mcp-code-indexer",
    packages=find_packages(),
    include_package_data=True,
    install_requires=requirements,
    extras_require=extras_require,
    entry_points={
        "console_scripts": [
            "mcp-indexer=mcp_code_indexer.cli:main",
            "mcp-server=server.unified_server:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
)
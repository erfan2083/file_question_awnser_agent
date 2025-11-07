"""Setup script for document-qa-system package."""

from setuptools import find_packages, setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="document-qa-system",
    version="1.0.0",
    author="Your Team",
    author_email="your.email@example.com",
    description="Intelligent Document Question Answering System with Multi-Agent Orchestration",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/document-qa-system",
    packages=find_packages(exclude=["tests*", "notebooks*"]),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.10",
    install_requires=[
        "langchain>=0.1.0",
        "langchain-google-genai>=0.0.6",
        "langgraph>=0.0.20",
        "google-generativeai>=0.3.2",
        "pypdf2>=3.0.1",
        "python-docx>=1.1.0",
        "Pillow>=10.1.0",
        "pytesseract>=0.3.10",
        "chromadb>=0.4.22",
        "rank-bm25>=0.2.2",
        "fastapi>=0.109.0",
        "streamlit>=1.30.0",
        "pydantic>=2.5.3",
        "pydantic-settings>=2.1.0",
        "loguru>=0.7.2",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.4",
            "pytest-cov>=4.1.0",
            "black>=23.12.1",
            "flake8>=7.0.0",
            "isort>=5.13.2",
            "mypy>=1.8.0",
            "pre-commit>=3.6.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "docqa-api=api.main:main",
            "docqa-ui=ui.streamlit_app:main",
        ],
    },
)

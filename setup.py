#!/usr/bin/env python3
"""
Setup script for CSS Analyzer package.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8') if (this_directory / "README.md").exists() else ""

# Read requirements
requirements = []
with open('requirements.txt') as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name="css-analyzer",
    version="1.0.0",
    author="CSS Analyzer Team",
    author_email="your-email@example.com",
    description="A comprehensive CLI tool for analyzing CSS and web project files",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-username/css-analyzer",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Quality Assurance",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Text Processing :: Markup :: HTML",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
    ],
    python_requires=">=3.7",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "css-analyzer=css_analyser.main:cli",
        ],
    },
    include_package_data=True,
    package_data={
        "css_analyser": ["templates/*.html"],
    },
    keywords="css analyzer web development duplicate selectors unused",
    project_urls={
        "Bug Reports": "https://github.com/your-username/css-analyzer/issues",
        "Source": "https://github.com/your-username/css-analyzer",
    },
)
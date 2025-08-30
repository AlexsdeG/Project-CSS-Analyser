"""
Utility functions for CSS Analyzer.
"""

import os
from pathlib import Path
from typing import List, Set
import fnmatch

# Default directories to exclude from analysis
DEFAULT_EXCLUDE_DIRS = {
    'node_modules',
    'vendor',
    '.git',
    '.svn',
    '.hg',
    '.idea',
    '.vscode',
    'build',
    'dist',
    'out',
    'coverage',
    '__pycache__',
    '.pytest_cache',
    'venv',
    'env',
    '.env',
    '.tox'
}

# Default file extensions to include
DEFAULT_CSS_EXTENSIONS = {'.css', '.scss', '.sass', '.less'}
DEFAULT_SOURCE_EXTENSIONS = {'.html', '.htm', '.php', '.js', '.jsx', '.ts', '.tsx', '.vue'}

def get_css_files(path: Path, exclude_dirs: Set[str] = None) -> List[Path]:
    """
    Get all CSS files from the given path.
    
    Args:
        path: Path to a file or directory
        exclude_dirs: Set of directory names to exclude from search
        
    Returns:
        List of CSS file paths
    """
    if exclude_dirs is None:
        exclude_dirs = DEFAULT_EXCLUDE_DIRS
    
    css_files = []
    
    if path.is_file():
        if path.suffix.lower() in DEFAULT_CSS_EXTENSIONS:
            css_files.append(path)
    elif path.is_dir():
        for root, dirs, files in os.walk(path):
            # Remove excluded directories
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            
            for file in files:
                file_path = Path(root) / file
                if file_path.suffix.lower() in DEFAULT_CSS_EXTENSIONS:
                    css_files.append(file_path)
    
    return sorted(css_files)

def get_source_files(path: Path, exclude_dirs: Set[str] = None) -> List[Path]:
    """
    Get all source files (HTML, PHP, JS) from the given path.
    
    Args:
        path: Path to a file or directory
        exclude_dirs: Set of directory names to exclude from search
        
    Returns:
        List of source file paths
    """
    if exclude_dirs is None:
        exclude_dirs = DEFAULT_EXCLUDE_DIRS
    
    source_files = []
    
    if path.is_file():
        if path.suffix.lower() in DEFAULT_SOURCE_EXTENSIONS:
            source_files.append(path)
    elif path.is_dir():
        for root, dirs, files in os.walk(path):
            # Remove excluded directories
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            
            for file in files:
                file_path = Path(root) / file
                if file_path.suffix.lower() in DEFAULT_SOURCE_EXTENSIONS:
                    source_files.append(file_path)
    
    return sorted(source_files)

def get_file_size(file_path: Path) -> int:
    """Get file size in bytes."""
    try:
        return file_path.stat().st_size
    except OSError:
        return 0

def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format."""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"

def read_file_content(file_path: Path, encoding: str = 'utf-8') -> str:
    """
    Read file content safely.
    
    Args:
        file_path: Path to the file
        encoding: File encoding (default: utf-8)
        
    Returns:
        File content as string, or empty string if error
    """
    try:
        with open(file_path, 'r', encoding=encoding) as f:
            return f.read()
    except (UnicodeDecodeError, IOError):
        # Try with different encodings
        for alt_encoding in ['latin-1', 'cp1252', 'utf-16']:
            try:
                with open(file_path, 'r', encoding=alt_encoding) as f:
                    return f.read()
            except IOError:
                continue
        return ""

def is_binary_file(file_path: Path) -> bool:
    """
    Check if a file is binary.
    
    Args:
        file_path: Path to the file
        
    Returns:
        True if file is binary, False otherwise
    """
    try:
        with open(file_path, 'rb') as f:
            chunk = f.read(1024)
            return b'\x00' in chunk
    except IOError:
        return False

def get_file_info(file_path: Path) -> dict:
    """
    Get comprehensive file information.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Dictionary with file information
    """
    try:
        stat = file_path.stat()
        return {
            'name': file_path.name,
            'path': str(file_path),
            'size': stat.st_size,
            'size_formatted': format_file_size(stat.st_size),
            'extension': file_path.suffix.lower(),
            'is_binary': is_binary_file(file_path),
            'modified_time': stat.st_mtime,
            'created_time': stat.st_ctime
        }
    except OSError:
        return {
            'name': file_path.name,
            'path': str(file_path),
            'size': 0,
            'size_formatted': '0 B',
            'extension': file_path.suffix.lower(),
            'is_binary': False,
            'modified_time': 0,
            'created_time': 0
        }

def find_files_by_pattern(path: Path, pattern: str, exclude_dirs: Set[str] = None) -> List[Path]:
    """
    Find files matching a pattern.
    
    Args:
        path: Path to search in
        pattern: Pattern to match (e.g., '*.css')
        exclude_dirs: Set of directory names to exclude from search
        
    Returns:
        List of matching file paths
    """
    if exclude_dirs is None:
        exclude_dirs = DEFAULT_EXCLUDE_DIRS
    
    matching_files = []
    
    if path.is_file():
        if fnmatch.fnmatch(path.name, pattern):
            matching_files.append(path)
    elif path.is_dir():
        for root, dirs, files in os.walk(path):
            # Remove excluded directories
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            
            for file in files:
                if fnmatch.fnmatch(file, pattern):
                    matching_files.append(Path(root) / file)
    
    return sorted(matching_files)

def create_directory(path: Path) -> bool:
    """
    Create directory if it doesn't exist.
    
    Args:
        path: Directory path to create
        
    Returns:
        True if directory was created or already exists, False otherwise
    """
    try:
        path.mkdir(parents=True, exist_ok=True)
        return True
    except OSError:
        return False

def is_valid_css_file(file_path: Path) -> bool:
    """
    Check if a file is a valid CSS file.
    
    Args:
        file_path: Path to the file
        
    Returns:
        True if file is a valid CSS file, False otherwise
    """
    if not file_path.is_file():
        return False
    
    if file_path.suffix.lower() not in DEFAULT_CSS_EXTENSIONS:
        return False
    
    if is_binary_file(file_path):
        return False
    
    return True

def is_valid_source_file(file_path: Path) -> bool:
    """
    Check if a file is a valid source file (HTML, PHP, JS).
    
    Args:
        file_path: Path to the file
        
    Returns:
        True if file is a valid source file, False otherwise
    """
    if not file_path.is_file():
        return False
    
    if file_path.suffix.lower() not in DEFAULT_SOURCE_EXTENSIONS:
        return False
    
    if is_binary_file(file_path):
        return False
    
    return True

def get_project_root(path: Path) -> Path:
    """
    Try to find the project root directory.
    
    Args:
        path: Starting path to search from
        
    Returns:
        Path to the project root, or the original path if no root found
    """
    current_path = path.absolute()
    
    # Look for common project root indicators
    root_indicators = {
        'package.json',
        'composer.json',
        'requirements.txt',
        'setup.py',
        'pyproject.toml',
        'Gemfile',
        'pom.xml',
        'build.gradle',
        '.git',
        '.svn',
        '.hg'
    }
    
    while current_path != current_path.parent:
        # Check if current directory contains any root indicators
        for indicator in root_indicators:
            if (current_path / indicator).exists():
                return current_path
        
        current_path = current_path.parent
    
    # If no root found, return the original path
    return path.absolute()

def clean_css_selector(selector: str) -> str:
    """
    Clean and normalize a CSS selector.
    
    Args:
        selector: Raw CSS selector
        
    Returns:
        Cleaned selector
    """
    # Remove extra whitespace
    selector = ' '.join(selector.split())
    
    # Remove newlines and tabs
    selector = selector.replace('\n', ' ').replace('\t', ' ')
    
    # Normalize multiple spaces
    while '  ' in selector:
        selector = selector.replace('  ', ' ')
    
    return selector.strip()

def extract_class_names(selector: str) -> List[str]:
    """
    Extract class names from a CSS selector.
    
    Args:
        selector: CSS selector string
        
    Returns:
        List of class names
    """
    import re
    
    # Find all class selectors (e.g., .class-name)
    class_pattern = r'\.([a-zA-Z0-9_-]+)'
    class_matches = re.findall(class_pattern, selector)
    
    return class_matches

def extract_id_names(selector: str) -> List[str]:
    """
    Extract ID names from a CSS selector.
    
    Args:
        selector: CSS selector string
        
    Returns:
        List of ID names
    """
    import re
    
    # Find all ID selectors (e.g., #id-name)
    id_pattern = r'#([a-zA-Z0-9_-]+)'
    id_matches = re.findall(id_pattern, selector)
    
    return id_matches
"""
Utility functions for CSS Analyzer.
"""

import os
from pathlib import Path
from typing import List, Set, Dict, Any, Tuple
import fnmatch
import re
from urllib.parse import quote

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

# Subset used for page parsing (entry documents)
PAGE_EXTENSIONS = {'.html', '.htm', '.php'}

# Default table cap used by reporters when --full is not specified
DEFAULT_TABLE_CAP = 10

# -------------------------------
# Path normalization and link helpers
# -------------------------------

def to_abs(p: Path) -> Path:
    return p.resolve()

def make_file_href(p: Path) -> str:
    """Build a file:/// URL for a filesystem path.

    Uses Path.as_uri() to produce a proper file URI that:
    - keeps the Windows drive colon unencoded (file:///D:/...),
    - percent-encodes unsafe characters (spaces -> %20, non-ASCII -> UTF-8 percent-encoded).
    """
    p = to_abs(p)
    try:
        return p.as_uri()
    except Exception:
        # Fallback: quote path but keep ':' and '/' safe (avoid encoding drive colon).
        return "file:///" + quote(p.as_posix(), safe='/:')
        

def make_vscode_href(p: Path, line: int | None = None) -> str:
    """Build a vscode:// deep link that opens a file (and optional line) in VS Code."""
    p = to_abs(p)
    # VS Code expects a POSIX-like path with drive letter (lowercase recommended)
    posix_path = p.as_posix()
    # Lowercase drive letter if present like 'D:/...'
    if re.match(r'^[A-Za-z]:/', posix_path):
        posix_path = posix_path[0].lower() + posix_path[1:]
    if line and isinstance(line, int) and line > 0:
        return f"vscode://file/{posix_path}:{line}"
    return f"vscode://file/{posix_path}"

def make_rel_label(p: Path, project_root: Path) -> str:
    """Return a label like "\\sample_project\\style.css" relative to project_root.

    If the path is outside the project root, returns "\\filename.ext".
    Always uses backslashes in the label per requirement.
    """
    p = to_abs(p)
    root = to_abs(project_root) if project_root else p.parent
    try:
        rel = p.relative_to(root)
    except ValueError:
        # If outside root, just show the file name
        return f"\\{p.name}"
    # Backslash separators in label, ensure no duplicate backslashes
    label = "\\" + str(rel).replace("/", "\\").replace("\\\\", "\\")
    return label

def make_console_link_text(label: str, href: str):
    """Return tuple (text, style) usable by rich for hyperlinks in console."""
    return (label, f"link {href} bold yellow")

def make_html_link(label: str, href: str) -> str:
    """Return a yellow-styled anchor tag for HTML reports."""
    return f'<a href="{href}" target="_blank" class="file-link">{label}</a>'

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

def _iter_files(path: Path, include_exts: Set[str], exclude_dirs: Set[str]) -> List[Path]:
    """Internal helper to iterate files by extensions under a path."""
    files: List[Path] = []
    if path.is_file():
        if path.suffix.lower() in include_exts:
            files.append(path)
    elif path.is_dir():
        for root, dirs, filenames in os.walk(path):
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            for name in filenames:
                p = Path(root) / name
                if p.suffix.lower() in include_exts:
                    files.append(p)
    return sorted(files)

def _resolve_path(base: Path, href: str) -> Path:
    """Resolve a possibly relative href against a base file path."""
    # Ignore external URLs
    if re.match(r'^(https?:)?//', href) or href.startswith('data:'):
        return None
    # Remove query/hash parts
    href_clean = re.split(r'[?#]', href)[0]
    resolved = (base.parent / href_clean).resolve()
    return resolved

def resolve_css_imports(entry_css: Path) -> List[Path]:
    """
    Resolve @import chains for a given CSS file.

    Depth-first traversal, returns a flattened ordered list where imported
    stylesheets appear before the importing stylesheet. Cycles are prevented.
    """
    visited: Set[Path] = set()
    ordered: List[Path] = []

    import_pattern = re.compile(r"@import\s+(?:url\(\s*)?[\'\"]?([^\'\"\)]+)")

    def dfs(css_path: Path):
        css_path = css_path.resolve()
        if css_path in visited or not css_path.exists():
            return
        visited.add(css_path)
        try:
            content = read_file_content(css_path)
        except Exception:
            content = ''

        for match in import_pattern.finditer(content):
            href = match.group(1).strip()
            child = _resolve_path(css_path, href)
            if child and child.suffix.lower() in DEFAULT_CSS_EXTENSIONS:
                if child in visited:
                    # cycle detected; skip further descent
                    continue
                dfs(child)
        ordered.append(css_path)

    dfs(entry_css)
    return ordered

def parse_html_for_css(path: Path, exclude_dirs: Set[str] = None) -> Dict[str, Any]:
    """
    Scan HTML/PHP pages to determine concrete CSS load order per page.

    Returns a dict with keys:
      - pages: { page_path: { 'css_chain': [css paths...], 'uncertain_css': [paths...] } }
      - all_css: set([...])
      - unreferenced_css: set([...])
    """
    if exclude_dirs is None:
        exclude_dirs = DEFAULT_EXCLUDE_DIRS

    pages: Dict[str, Dict[str, Any]] = {}
    all_css: Set[str] = set()
    uncertain_css: Dict[str, Set[str]] = {}

    page_files = _iter_files(path, PAGE_EXTENSIONS, exclude_dirs)

    # Patterns
    link_pattern = re.compile(r"<link[^>]+rel=[\"\']stylesheet[\"\'][^>]*href=[\"\']([^\"\']+)[\"\']", re.IGNORECASE)
    style_import_pattern = re.compile(r"@import\s+(?:url\(\s*)?[\'\"]?([^\'\"\)]+)", re.IGNORECASE)
    script_src_pattern = re.compile(r"<script[^>]*src=[\"\']([^\"\']+)[\"\']", re.IGNORECASE)

    js_dynamic_link_patterns = [
        re.compile(r"createElement\(\s*['\"]link['\"]\s*\)", re.IGNORECASE),
        re.compile(r"\.setAttribute\(\s*['\"]rel['\"],\s*['\"]stylesheet['\"]\s*\)", re.IGNORECASE),
        re.compile(r"\.href\s*=\s*['\"]([^'\"]+)['\"]", re.IGNORECASE),
    ]

    # Collect JS files referenced by pages (to narrow dynamic detection scope)
    js_files_for_pages: Dict[Path, List[Path]] = {}

    # -------------------------------
    # PHP scanning helpers
    # -------------------------------
    # Capture define('CONST', 'value'); string values only
    define_pattern = re.compile(r"define\(\s*['\"]([A-Z0-9_]+)['\"]\s*,\s*['\"]([^'\"]*)['\"]\s*\)", re.IGNORECASE)
    # wp_enqueue_style( ..., "path.css" )
    enqueue_style_string = re.compile(r"wp_(?:enqueue|register)_style\s*\(\s*[^,]*,\s*['\"]([^'\"]+\.css)['\"]", re.IGNORECASE)
    # wp_enqueue_style( ..., CONST . 'path.css' )
    enqueue_style_const_concat = re.compile(r"wp_(?:enqueue|register)_style\s*\(\s*[^,]*,\s*([A-Z_][A-Z0-9_]*)\s*\.\s*['\"]([^'\"]+\.css)['\"]", re.IGNORECASE)
    # wp_enqueue_style( ..., plugins_url('path.css', ...) )
    enqueue_style_plugins_url = re.compile(r"wp_(?:enqueue|register)_style\s*\(\s*[^,]*,\s*plugins_url\s*\(\s*['\"]([^'\"]+\.css)['\"][^)]*\)", re.IGNORECASE)
    # wp_enqueue_style( ..., plugin_dir_url(__FILE__) . 'path.css' )
    enqueue_style_plugin_dir_url_concat = re.compile(r"wp_(?:enqueue|register)_style\s*\(\s*[^,]*,\s*plugin_dir_url\s*\(\s*__FILE__\s*\)\s*\.\s*['\"]([^'\"]+\.css)['\"]", re.IGNORECASE)
    # wp_enqueue_style( ..., get_stylesheet_directory_uri() . '/path.css' ) or get_template_directory_uri()
    enqueue_style_theme_dir_uri_concat = re.compile(r"wp_(?:enqueue|register)_style\s*\(\s*[^,]*,\s*get_(?:stylesheet|template)_directory_uri\s*\(\s*\)\s*\.\s*['\"]([^'\"]+\.css)['\"]", re.IGNORECASE)
    # include/require patterns with string literal
    php_include_literal = re.compile(r"(?:include|include_once|require|require_once)\s*\(\s*['\"]([^'\"]+\.php)['\"]\s*\)", re.IGNORECASE)
    # include/require with CONST . 'file.php'
    php_include_const_concat = re.compile(r"(?:include|include_once|require|require_once)\s*\(\s*([A-Z_][A-Z0-9_]*)\s*\.\s*['\"]([^'\"]+\.php)['\"]\s*\)", re.IGNORECASE)

    # Gather PHP defines across the workspace under path for resolving constants
    def _gather_php_defines(root: Path) -> Dict[str, Dict[str, Any]]:
        consts: Dict[str, Dict[str, Any]] = {}
        php_files = _iter_files(root, {'.php'}, exclude_dirs)
        for pf in php_files:
            try:
                txt = read_file_content(pf)
            except Exception:
                continue
            for m in define_pattern.finditer(txt):
                name = m.group(1)
                val = m.group(2)
                consts[name] = {'value': val, 'file': str(pf.resolve())}
        return consts

    php_constants = _gather_php_defines(path)

    # Resolve a CSS asset path from different PHP enqueue patterns
    def _resolve_css_from_php(expr_type: str, page_file: Path, match: re.Match) -> Path | None:
        try:
            if expr_type == 'string':
                raw = match.group(1)
                return _resolve_asset_path(raw, page_file, php_constants)
            if expr_type == 'const_concat':
                const = match.group(1)
                tail = match.group(2)
                # If tail is absolute-like '/foo/bar.css', try suffix search in project
                if tail.startswith('/'):
                    cand = _find_css_by_suffix(path, tail.lstrip('/'))
                    if cand:
                        return cand
                base = None
                info = php_constants.get(const)
                if info:
                    base_val = info.get('value') or ''
                    # Prefer PATH-like constants as base directory
                    if ('PATH' in const or 'DIR' in const) and base_val:
                        b = Path(base_val)
                        if b.exists():
                            base = b
                # Fallback: directory of the page_file
                if base is None:
                    # Try to find the tail by walking up the tree
                    found = _find_upwards_for_tail(page_file, tail)
                    if found:
                        return found
                    base = page_file.parent
                return (base / tail).resolve()
            if expr_type == 'plugins_url':
                tail = match.group(1)
                if tail.startswith('/'):
                    cand = _find_css_by_suffix(path, tail.lstrip('/'))
                    if cand:
                        return cand
                # Try to locate by walking up from current file
                found = _find_upwards_for_tail(page_file, tail)
                if found:
                    return found
                return (page_file.parent / tail).resolve()
            if expr_type == 'plugin_dir_url_concat':
                tail = match.group(1)
                if tail.startswith('/'):
                    cand = _find_css_by_suffix(path, tail.lstrip('/'))
                    if cand:
                        return cand
                found = _find_upwards_for_tail(page_file, tail)
                if found:
                    return found
                return (page_file.parent / tail).resolve()
            if expr_type == 'theme_dir_uri_concat':
                tail = match.group(1)
                if tail.startswith('/'):
                    cand = _find_css_by_suffix(path, tail.lstrip('/'))
                    if cand:
                        return cand
                found = _find_upwards_for_tail(page_file, tail)
                if found:
                    return found
                return (page_file.parent / tail).resolve()
        except Exception:
            return None
        return None

    # Resolve asset path or URL-ish string to local Path if possible
    def _resolve_asset_path(raw: str, base_file: Path, consts: Dict[str, Dict[str, Any]]) -> Path | None:
        # If absolute filesystem path
        try:
            p = Path(raw)
            if p.suffix.lower() == '.css' and p.exists():
                return p.resolve()
        except Exception:
            pass
        # If URL, take the path part and try to map to local by suffix search
        if re.match(r'^https?://', raw) or raw.startswith('//'):
            try:
                from urllib.parse import urlparse
                u = urlparse(raw if raw.startswith('http') else 'http:' + raw)
                url_path = u.path.lstrip('/')
                cand = _find_css_by_suffix(path, url_path)
                if cand:
                    return cand
            except Exception:
                pass
        # Treat as relative path
        rel = raw.strip()
        # Normalize potential concatenated slashes
        rel = rel.replace('\\', '/').replace('//', '/')
        candidate = (base_file.parent / rel).resolve()
        if candidate.suffix.lower() == '.css' and candidate.exists():
            return candidate
        # If startswith '/', attempt suffix search in project
        if rel.startswith('/'):
            cand = _find_css_by_suffix(path, rel.lstrip('/'))
            if cand:
                return cand
        return None

    def _find_css_by_suffix(root: Path, suffix: str) -> Path | None:
        """Find a CSS file under root that ends with the given suffix (path fragment)."""
        suffix_norm = suffix.replace('\\', '/').lower()
        for f in _iter_files(root, DEFAULT_CSS_EXTENSIONS, exclude_dirs):
            try:
                s = str(f.resolve()).replace('\\', '/').lower()
                if s.endswith(suffix_norm):
                    return f.resolve()
            except Exception:
                continue
        return None

    def _find_upwards_for_tail(start_file: Path, tail: str, max_levels: int = 6) -> Path | None:
        """From start_file directory, walk up to max_levels and check for tail path existence."""
        tail_norm = tail.replace('\\', '/')
        cur = start_file.parent
        for _ in range(max_levels):
            candidate = (cur / tail_norm).resolve()
            if candidate.exists() and candidate.suffix.lower() == '.css':
                return candidate
            if cur == cur.parent:
                break
            cur = cur.parent
        return None

    # Additional patterns for include/require variations
    php_include_dirname = re.compile(r"(?:include|include_once|require|require_once)\s*\(\s*dirname\(\s*__FILE__\s*\)\s*\\.\s*['\"]([^'\"]+\.php)['\"]\s*\)", re.IGNORECASE)
    php_include_dir = re.compile(r"(?:include|include_once|require|require_once)\s*\(\s*__DIR__\s*\\.\s*['\"]([^'\"]+\.php)['\"]\s*\)", re.IGNORECASE)
    php_include_plugin_dir_path = re.compile(r"(?:include|include_once|require|require_once)\s*\(\s*plugin_dir_path\s*\(\s*__FILE__\s*\)\s*\\.\s*['\"]([^'\"]+\.php)['\"]\s*\)", re.IGNORECASE)
    php_include_theme_dir = re.compile(r"(?:include|include_once|require|require_once)\s*\(\s*get_(?:stylesheet|template)_directory\s*\(\s*\)\s*\\.\s*['\"]([^'\"]+\.php)['\"]\s*\)", re.IGNORECASE)

    # Register/enqueue by handle patterns
    register_style_string = re.compile(r"wp_register_style\s*\(\s*['\"]([^'\"]+)['\"]\s*,\s*['\"]([^'\"]+\.css)['\"]", re.IGNORECASE)
    register_style_const_concat = re.compile(r"wp_register_style\s*\(\s*['\"]([^'\"]+)['\"]\s*,\s*([A-Z_][A-Z0-9_]*)\s*\.\s*['\"]([^'\"]+\.css)['\"]", re.IGNORECASE)
    register_style_plugins_url = re.compile(r"wp_register_style\s*\(\s*['\"]([^'\"]+)['\"]\s*,\s*plugins_url\s*\(\s*['\"]([^'\"]+\.css)['\"][^)]*\)", re.IGNORECASE)
    register_style_plugin_dir_url_concat = re.compile(r"wp_register_style\s*\(\s*['\"]([^'\"]+)['\"]\s*,\s*plugin_dir_url\s*\(\s*__FILE__\s*\)\s*\.\s*['\"]([^'\"]+\.css)['\"]", re.IGNORECASE)
    register_style_theme_dir_uri_concat = re.compile(r"wp_register_style\s*\(\s*['\"]([^'\"]+)['\"]\s*,\s*get_(?:stylesheet|template)_directory_uri\s*\(\s*\)\s*\.\s*['\"]([^'\"]+\.css)['\"]", re.IGNORECASE)
    enqueue_handle_pattern = re.compile(r"wp_enqueue_style\s*\(\s*['\"]([^'\"]+)['\"]", re.IGNORECASE)

    def _scan_php_for_css(page: Path, visited: Set[Path], handle_map: Dict[str, Path], enqueued_handles: Set[str]) -> Tuple[List[Path], List[Path]]:
        """Return (css_files, included_php_files) found in a PHP file. Updates handle_map and enqueued_handles in place."""
        css_found: List[Path] = []
        includes: List[Path] = []
        if page in visited:
            return css_found, includes
        visited.add(page)
        txt = read_file_content(page)
        if not txt:
            return css_found, includes
        # Register style patterns to populate handle_map
        for m in register_style_string.finditer(txt):
            handle = m.group(1)
            pth = _resolve_css_from_php('string', page, m)
            if pth and pth.exists():
                handle_map[handle] = pth
        for m in register_style_const_concat.finditer(txt):
            handle = m.group(1)
            # build a fake match-like object for const_concat for _resolve_css_from_php expectations
            # Here groups are (handle, CONST, tail), but resolver expects (CONST, tail)
            class _M:
                def __init__(self, const, tail):
                    self._const = const
                    self._tail = tail
                def group(self, idx):
                    if idx == 1:
                        return self._const
                    if idx == 2:
                        return self._tail
                    raise IndexError
            pth = _resolve_css_from_php('const_concat', page, _M(m.group(2), m.group(3)))
            if pth and pth.exists():
                handle_map[handle] = pth
        for m in register_style_plugins_url.finditer(txt):
            handle = m.group(1)
            class _M2:
                def __init__(self, tail):
                    self._tail = tail
                def group(self, idx):
                    if idx == 1:
                        return self._tail
                    raise IndexError
            pth = _resolve_css_from_php('plugins_url', page, _M2(m.group(2)))
            if pth and pth.exists():
                handle_map[handle] = pth
        for m in register_style_plugin_dir_url_concat.finditer(txt):
            handle = m.group(1)
            class _M3:
                def __init__(self, tail):
                    self._tail = tail
                def group(self, idx):
                    if idx == 1:
                        return self._tail
                    raise IndexError
            pth = _resolve_css_from_php('plugin_dir_url_concat', page, _M3(m.group(2)))
            if pth and pth.exists():
                handle_map[handle] = pth
        for m in register_style_theme_dir_uri_concat.finditer(txt):
            handle = m.group(1)
            class _M4:
                def __init__(self, tail):
                    self._tail = tail
                def group(self, idx):
                    if idx == 1:
                        return self._tail
                    raise IndexError
            pth = _resolve_css_from_php('theme_dir_uri_concat', page, _M4(m.group(2)))
            if pth and pth.exists():
                handle_map[handle] = pth
        # Enqueue patterns
        for m in enqueue_style_string.finditer(txt):
            pth = _resolve_css_from_php('string', page, m)
            if pth and pth.exists():
                css_found.append(pth)
        for m in enqueue_style_const_concat.finditer(txt):
            pth = _resolve_css_from_php('const_concat', page, m)
            if pth and pth.exists():
                css_found.append(pth)
        for m in enqueue_style_plugins_url.finditer(txt):
            pth = _resolve_css_from_php('plugins_url', page, m)
            if pth and pth.exists():
                css_found.append(pth)
        for m in enqueue_style_plugin_dir_url_concat.finditer(txt):
            pth = _resolve_css_from_php('plugin_dir_url_concat', page, m)
            if pth and pth.exists():
                css_found.append(pth)
        for m in enqueue_style_theme_dir_uri_concat.finditer(txt):
            pth = _resolve_css_from_php('theme_dir_uri_concat', page, m)
            if pth and pth.exists():
                css_found.append(pth)
        # Enqueue by handle; resolve later after includes scanned
        for m in enqueue_handle_pattern.finditer(txt):
            handle = m.group(1)
            enqueued_handles.add(handle)
        # Includes
        for m in php_include_literal.finditer(txt):
            inc_rel = m.group(1)
            inc_path = (page.parent / inc_rel).resolve()
            if inc_path.exists() and inc_path.suffix.lower() == '.php':
                includes.append(inc_path)
        for m in php_include_const_concat.finditer(txt):
            const = m.group(1)
            tail = m.group(2)
            base = None
            info = php_constants.get(const)
            if info:
                base_val = info.get('value') or ''
                if ('PATH' in const or 'DIR' in const) and base_val:
                    b = Path(base_val)
                    if b.exists():
                        base = b
            if base is None:
                base = page.parent
            inc_path = (base / tail).resolve()
            if inc_path.exists() and inc_path.suffix.lower() == '.php':
                includes.append(inc_path)
        # dirname(__FILE__) . '/inc/foo.php'
        for m in php_include_dirname.finditer(txt):
            tail = m.group(1)
            inc_path = (page.parent / tail.lstrip('/')).resolve()
            if inc_path.exists() and inc_path.suffix.lower() == '.php':
                includes.append(inc_path)
        # __DIR__ . '/inc/foo.php'
        for m in php_include_dir.finditer(txt):
            tail = m.group(1)
            inc_path = (page.parent / tail.lstrip('/')).resolve()
            if inc_path.exists() and inc_path.suffix.lower() == '.php':
                includes.append(inc_path)
        # plugin_dir_path(__FILE__) . 'includes/foo.php'
        for m in php_include_plugin_dir_path.finditer(txt):
            tail = m.group(1)
            found = _find_upwards_for_tail(page, tail)
            if found and found.suffix.lower() == '.php':
                includes.append(found)
        # get_template_directory() . '/inc/foo.php' or get_stylesheet_directory()
        for m in php_include_theme_dir.finditer(txt):
            tail = m.group(1)
            found = _find_upwards_for_tail(page, tail)
            if found and found.suffix.lower() == '.php':
                includes.append(found)
        return css_found, includes

    for page in page_files:
        content = read_file_content(page)
        # Ordered <link> tags
        hrefs = link_pattern.findall(content)
        css_chain: List[str] = []

        for href in hrefs:
            p = _resolve_path(page, href)
            if p and p.suffix.lower() in DEFAULT_CSS_EXTENSIONS:
                # Resolve imports for this stylesheet
                flattened = resolve_css_imports(p)
                for f in flattened:
                    css_chain.append(str(f.resolve()))
                    all_css.add(str(f.resolve()))

        # Inline <style> @import
        for import_href in style_import_pattern.findall(content):
            p = _resolve_path(page, import_href)
            if p and p.suffix.lower() in DEFAULT_CSS_EXTENSIONS:
                flattened = resolve_css_imports(p)
                for f in flattened:
                    css_chain.append(str(f.resolve()))
                    all_css.add(str(f.resolve()))

        # If PHP file, scan for enqueued CSS and included PHP files (recursive)
        if page.suffix.lower() == '.php':
            visited_php: Set[Path] = set()
            to_scan: List[Path] = [page]
            depth = 0
            max_depth = 2  # prevent deep recursion
            handle_map: Dict[str, Path] = {}
            enqueued_handles: Set[str] = set()
            while to_scan and depth <= max_depth:
                next_round: List[Path] = []
                for php_file in to_scan:
                    css_paths, includes = _scan_php_for_css(php_file, visited_php, handle_map, enqueued_handles)
                    for cp in css_paths:
                        flattened = resolve_css_imports(cp)
                        for f in flattened:
                            css_chain.append(str(f.resolve()))
                            all_css.add(str(f.resolve()))
                    for inc in includes:
                        if inc not in visited_php:
                            next_round.append(inc)
                to_scan = next_round
                depth += 1
            # After scanning all related PHP files, resolve any enqueued handles
            for h in sorted(enqueued_handles):
                pth = handle_map.get(h)
                if pth and pth.exists():
                    flattened = resolve_css_imports(pth)
                    for f in flattened:
                        css_chain.append(str(f.resolve()))
                        all_css.add(str(f.resolve()))

        # JS included scripts for this page
        js_srcs = script_src_pattern.findall(content)
        page_js: List[Path] = []
        for js in js_srcs:
            jp = _resolve_path(page, js)
            if jp and jp.suffix.lower() in {'.js', '.mjs'} and jp.exists():
                page_js.append(jp)
        js_files_for_pages[page] = page_js

        pages[str(page)] = {
            'css_chain': css_chain,
            'uncertain_css': []  # fill later
        }

    # Very naive dynamic detection inside JS: look for href assignments or link creation
    for page, js_paths in js_files_for_pages.items():
        uncertain: Set[str] = set()
        for jp in js_paths:
            js_content = read_file_content(jp)
            if not js_content:
                continue
            # If code mentions link creation and sets href, mark as uncertain
            if any(patt.search(js_content) for patt in js_dynamic_link_patterns):
                # Try to extract explicit href values
                for m in js_dynamic_link_patterns[2].finditer(js_content):
                    href = m.group(1)
                    p = _resolve_path(jp, href)
                    if p and p.suffix.lower() in DEFAULT_CSS_EXTENSIONS:
                        uncertain.add(str(p.resolve()))
        if str(page) in pages:
            pages[str(page)]['uncertain_css'] = sorted(uncertain)
            for u in uncertain:
                all_css.add(u)

    # Determine unreferenced CSS: all CSS on filesystem under path minus discovered
    all_fs_css = set(str(p.resolve()) for p in _iter_files(path, DEFAULT_CSS_EXTENSIONS, exclude_dirs))
    unreferenced_css = sorted(all_fs_css - set(all_css))

    return {
        'pages': pages,
        'all_css': sorted(set(all_css)),
        'unreferenced_css': unreferenced_css
    }

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
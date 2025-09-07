"""
Core analysis modules for CSS Analyzer.
"""

import re
import cssutils
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Set, Tuple, Any
import logging
import warnings

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Suppress cssutils warnings
warnings.filterwarnings('ignore', module='cssutils')

class BaseAnalyzer:
    """Base class for all analyzers."""
    
    def __init__(self):
        self.css_parser = cssutils.CSSParser()
        self.errors = []
        self.last_positions = defaultdict(lambda: defaultdict(int))  # file -> rule_text -> last_pos
        
        # Suppress cssutils warnings
        cssutils.log.setLevel(logging.CRITICAL)
    
    
    def _parse_css_file(self, file_path: Path) -> Tuple[cssutils.css.CSSStyleSheet, str]:
        """Parse a CSS file and return the stylesheet object and content."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                css_content = f.read()
            stylesheet = self.css_parser.parseString(css_content)
            return stylesheet, css_content
        except Exception as e:
            self.errors.append(f"Error parsing {file_path}: {str(e)}")
            return None, ""
    
    def _get_line_number(self, css_content: str, rule_text: str, file_path: str = None) -> int:
        """Calculate the line number of a rule in the CSS content."""
        # Determine the pattern based on the type of rule_text
        if rule_text.startswith('/*') and rule_text.endswith('*/'):
            # Comment
            pattern = re.escape(rule_text)
        elif rule_text.startswith('@media'):
            # Media query
            pattern = re.escape(rule_text)
        else:
            # Selector
            pattern = re.escape(rule_text) + r'\s*\{'
        
        # Find all matches
        matches = list(re.finditer(pattern, css_content))
        if not matches:
            return 0
        
        # Find the next match after last_pos
        last_pos = self.last_positions[file_path][rule_text] if file_path else 0
        for match in matches:
            if match.start() > last_pos:
                self.last_positions[file_path][rule_text] = match.end()
                return css_content[:match.start()].count('\n') + 1
        
        # If no more matches after last_pos, return 0 or the last match's line
        return 0
    

class DuplicateAnalyzer(BaseAnalyzer):
    """Analyzer for finding duplicate CSS selectors, media queries, and comments."""
    
    def analyze(self, css_files: List[Path], merge: bool = False, page_map: Dict[str, Any] = None, per_page_merge: bool = False, skip_unreferenced: bool = False) -> Dict[str, Any]:
        """Analyze CSS files for duplicates.

        Args:
            css_files: List of CSS files to analyze
            merge: When True, produce merged CSS blocks honoring cascade
            page_map: Either a dict of pages -> {css_chain, uncertain_css} or the
                      full parse_html_for_css() result containing keys 'pages',
                      'all_css', 'unreferenced_css'. If provided, merging and
                      warnings will respect per-page load order and ignore
                      unreferenced CSS in global merge.
            per_page_merge: When True, also compute merged CSS per page.
        """
        results = {
            'selectors': defaultdict(list),
            'media_queries': defaultdict(list),
            'comments': defaultdict(list),
            'errors': [],
            'warnings': [],
        }

        # Normalize page mapping
        pages = None
        unreferenced_css = []
        if page_map:
            if 'pages' in page_map:
                pages = page_map.get('pages', {})
                unreferenced_css = page_map.get('unreferenced_css', [])
            else:
                pages = page_map
            # Attach per-page load order (only non-empty chains) if pages available
            if pages:
                results['load_order'] = {
                    k: (v.get('css_chain', []) or [])
                    for k, v in pages.items()
                    if v.get('css_chain')
                }
        if unreferenced_css:
            results['unreferenced_css'] = list(unreferenced_css)
        
        # Optionally filter css_files to only those referenced by pages
        if pages and skip_unreferenced:
            referenced: Set[str] = set()
            for _, info in pages.items():
                for p in info.get('css_chain', []) or []:
                    referenced.add(str(Path(p).resolve()))
            css_files = [Path(p).resolve() for p in css_files if str(Path(p).resolve()) in referenced]
        
        for css_file in css_files:
            stylesheet, css_content = self._parse_css_file(css_file)
            if not stylesheet:
                continue
            
            for rule in stylesheet:
                if isinstance(rule, cssutils.css.CSSStyleRule):
                    # Handle CSS selectors
                    selector = rule.selectorText
                    if selector:
                        line = self._get_line_number(css_content, rule.selectorText, str(css_file))
                        location = {
                            'file': str(Path(css_file).resolve()),
                            'line': line
                        }
                        if merge:
                            location['rule'] = rule
                        results['selectors'][selector].append(location)
                
                elif isinstance(rule, cssutils.css.CSSMediaRule):
                    # Handle media queries
                    media_query = rule.media.mediaText
                    if media_query:
                        line = self._get_line_number(css_content, "@media " + rule.media.mediaText, str(css_file))
                        results['media_queries'][media_query].append({
                            'file': str(Path(css_file).resolve()),
                            'line': line
                        })
                    
                    # Also check rules within media queries
                    for inner_rule in rule:
                        if isinstance(inner_rule, cssutils.css.CSSStyleRule):
                            selector = inner_rule.selectorText
                            if selector:
                                line = self._get_line_number(css_content, inner_rule.selectorText, str(css_file))
                                location = {
                                    'file': str(Path(css_file).resolve()),
                                    'line': line
                                }
                                if merge:
                                    location['rule'] = inner_rule
                                results['selectors'][selector].append(location)
                
                elif isinstance(rule, cssutils.css.CSSComment):
                    # Handle comments
                    comment = rule.cssText
                    if comment and comment.strip():
                        line = self._get_line_number(css_content, rule.cssText, str(css_file))
                        results['comments'][comment].append({
                            'file': str(Path(css_file).resolve()),
                            'line': line
                        })
        
        # Filter to keep only duplicates
        results['selectors'] = {k: v for k, v in results['selectors'].items() if len(v) > 1}
        results['media_queries'] = {k: v for k, v in results['media_queries'].items() if len(v) > 1}
        results['comments'] = {k: v for k, v in results['comments'].items() if len(v) > 1}
        
        # Helper: format merged CSS from a prop map
        def format_merged_block(selector: str, merged_props: Dict[str, Dict[str, str]]) -> str:
            merged_style = cssutils.css.CSSStyleDeclaration()
            for name, data in merged_props.items():
                merged_style.setProperty(name, data['value'], data['priority'])
            properties = []
            for prop in merged_style:
                important = ' !important' if prop.priority == 'important' else ''
                properties.append(f"    {prop.name}: {prop.value}{important};")
            return f"{selector} {{\n" + "\n".join(properties) + "\n}"

        # Helper: merge a list of locations in a specified order and collect warnings
        def merge_locations(selector: str, ordered_locs: List[Dict[str, Any]], page: str = None) -> Tuple[Dict[str, Dict[str, str]], List[Dict[str, Any]]]:
            merged_props: Dict[str, Dict[str, str]] = {}
            prop_origin: Dict[str, Dict[str, Any]] = {}  # name -> origin location
            warnings_local: List[Dict[str, Any]] = []
            for loc in ordered_locs:
                if 'rule' not in loc:
                    continue
                for prop in loc['rule'].style:
                    name = prop.name
                    value = prop.value
                    priority = prop.priority
                    origin = {'file': loc['file'], 'line': loc['line']}

                    if name not in merged_props:
                        merged_props[name] = {'value': value, 'priority': priority}
                        prop_origin[name] = origin
                        continue

                    existing_priority = merged_props[name]['priority']
                    existing_origin = prop_origin[name]

                    if existing_priority == 'important' and priority != 'important':
                        # Important blocks normal later declaration
                        warnings_local.append({
                            'type': 'important-blocks-normal',
                            'selector': selector,
                            'property': name,
                            'from': f"{existing_origin['file']}:{existing_origin['line']}",
                            'to': f"{origin['file']}:{origin['line']}",
                            'reason': 'Earlier !important prevents later normal declaration from applying',
                            'page': page
                        })
                        continue

                    if priority == 'important' and existing_priority != 'important':
                        # Later important overrides earlier normal
                        warnings_local.append({
                            'type': 'later-overrides-earlier',
                            'selector': selector,
                            'property': name,
                            'from': f"{existing_origin['file']}:{existing_origin['line']}",
                            'to': f"{origin['file']}:{origin['line']}",
                            'reason': 'Later !important overrides earlier normal',
                            'page': page
                        })
                        merged_props[name] = {'value': value, 'priority': priority}
                        prop_origin[name] = origin
                        continue

                    # Same priority case
                    if priority == existing_priority == 'important':
                        warnings_local.append({
                            'type': 'important-vs-important',
                            'selector': selector,
                            'property': name,
                            'from': f"{existing_origin['file']}:{existing_origin['line']}",
                            'to': f"{origin['file']}:{origin['line']}",
                            'reason': 'Later !important overrides earlier !important',
                            'page': page
                        })
                    elif priority == existing_priority:
                        warnings_local.append({
                            'type': 'later-overrides-earlier',
                            'selector': selector,
                            'property': name,
                            'from': f"{existing_origin['file']}:{existing_origin['line']}",
                            'to': f"{origin['file']}:{origin['line']}",
                            'reason': 'Later declaration overrides earlier declaration',
                            'page': page
                        })

                    # Replace in both same-priority cases
                    merged_props[name] = {'value': value, 'priority': priority}
                    prop_origin[name] = origin

            return merged_props, warnings_local

        # Build a quick lookup of line ordering per file to ensure stable sort within file
        def sort_key_for_page(page_css_order: List[str], loc: Dict[str, Any]) -> Tuple[int, int]:
            file_to_index = {p: i for i, p in enumerate(page_css_order)}
            fi = file_to_index.get(loc['file'], 10**9)
            li = loc.get('line') or 10**6
            return (fi, li)

        if merge and results['selectors']:
            # Global merged (filtered to referenced CSS if pages provided)
            results['merged'] = {}
            referenced_css: Set[str] = set()
            if pages:
                for pg in pages.values():
                    for p in pg.get('css_chain', []):
                        referenced_css.add(p)
            # Determine a global order from pages if available
            global_order: List[str] = []
            if pages:
                seen: Set[str] = set()
                for page_path, pdata in pages.items():
                    for cssp in pdata.get('css_chain', []):
                        if cssp not in seen:
                            seen.add(cssp)
                            global_order.append(cssp)
                # Append any referenced CSS not in any chain (shouldn't happen often)
                for cssp in sorted(referenced_css):
                    if cssp not in seen:
                        global_order.append(cssp)

                # If pages have differing orders, emit an ambiguity warning
                chains = {tuple(pdata.get('css_chain', [])) for pdata in pages.values()}
                if len(chains) > 1:
                    results['warnings'].append({
                        'type': 'ambiguous-load-order',
                        'selector': '*',
                        'property': '*',
                        'from': '-',
                        'to': '-',
                        'reason': 'Multiple pages have different CSS load orders; consider --per-page-merge for accuracy',
                        'page': None
                    })

            def sort_key_global(loc: Dict[str, Any]) -> Tuple[int, int]:
                if not pages:
                    return (0, loc.get('line') or 0)
                file_index = global_order.index(loc['file']) if loc['file'] in global_order else 10**9
                return (file_index, loc.get('line') or 0)

            for selector, locations in results['selectors'].items():
                locs = [l for l in locations if 'rule' in l and (not pages or l['file'] in referenced_css)]
                if pages:
                    locs = sorted(locs, key=sort_key_global)
                # Merge and collect warnings
                merged_props, warn = merge_locations(selector, locs)
                if warn:
                    results['warnings'].extend(warn)
                results['merged'][selector] = format_merged_block(selector, merged_props)

            # Per-page merge
            if per_page_merge and pages:
                results['merged_per_page'] = {}
                for page_path, pdata in pages.items():
                    order = pdata.get('css_chain', [])
                    merged_for_page: Dict[str, str] = {}
                    for selector, locations in results['selectors'].items():
                        ordered_locs = sorted([l for l in locations if 'rule' in l], key=lambda l: sort_key_for_page(order, l))
                        # Keep only those files that actually appear in this page
                        ordered_locs = [l for l in ordered_locs if l['file'] in set(order)]
                        if not ordered_locs:
                            continue
                        merged_props, warn = merge_locations(selector, ordered_locs, page=page_path)
                        if warn:
                            results['warnings'].extend(warn)
                        merged_for_page[selector] = format_merged_block(selector, merged_props)
                    results['merged_per_page'][page_path] = merged_for_page

            # If pages known and some CSS appear as uncertain/dynamic, emit a general warning
            if pages:
                for page_path, pdata in pages.items():
                    uncertain = pdata.get('uncertain_css') or []
                    if uncertain:
                        results['warnings'].append({
                            'type': 'dynamic-css',
                            'selector': '*',
                            'property': '*',
                            'from': '-',
                            'to': '-',
                            'reason': f"Page has dynamically injected CSS with uncertain load order: {len(uncertain)} file(s)",
                            'page': page_path
                        })
                
        results['errors'] = self.errors
        
        return results

class UnusedSelectorAnalyzer(BaseAnalyzer):
    """Analyzer for finding unused CSS selectors."""
    
    def __init__(self):
        super().__init__()
        # Regex patterns for finding selectors in HTML/PHP/JS files
        self.class_pattern = re.compile(r'class\s*=\s*["\'][^"\']*?\b([a-zA-Z0-9_-]+)\b')
        self.id_pattern = re.compile(r'id\s*=\s*["\'][^"\']*?\b([a-zA-Z0-9_-]+)\b')
        
        # Common exclusions (framework classes, utility classes that might be dynamically added)
        self.excluded_selectors = {
            'active', 'disabled', 'hidden', 'visible', 'focus', 'hover', 'visited',
            'first', 'last', 'odd', 'even', 'selected', 'checked', 'required',
            'error', 'success', 'warning', 'info', 'primary', 'secondary',
            'sm', 'md', 'lg', 'xl', 'xs', 'row', 'col', 'container', 'wrapper'
        }

    def _extract_css_selectors(self, css_files: List[Path]) -> Dict[str, List[Dict[str, Any]]]:
        """Extract all CSS selectors with their locations."""
        selectors = defaultdict(list)
        
        for css_file in css_files:
            stylesheet, css_content = self._parse_css_file(css_file)
            if not stylesheet:
                continue
            
            for rule in stylesheet:
                if isinstance(rule, cssutils.css.CSSStyleRule):
                    # Parse selector text to extract individual class and ID names
                    selector_text = rule.selectorText
                    line = self._get_line_number(css_content, rule.selectorText, str(css_file))
                    
                    # Extract class selectors
                    class_matches = re.findall(r'\.([a-zA-Z0-9_-]+)', selector_text)
                    for match in class_matches:
                        if match not in self.excluded_selectors:
                            selector = f".{match}"
                            selectors[selector].append({
                                'file': str(Path(css_file).resolve()),
                                'line': line
                            })
                    
                    # Extract ID selectors
                    id_matches = re.findall(r'#([a-zA-Z0-9_-]+)', selector_text)
                    for match in id_matches:
                        if match not in self.excluded_selectors:
                            selector = f"#{match}"
                            selectors[selector].append({
                                'file': str(Path(css_file).resolve()),
                                'line': line
                            })
                
                elif isinstance(rule, cssutils.css.CSSMediaRule):
                    # Check rules within media queries
                    for inner_rule in rule:
                        if isinstance(inner_rule, cssutils.css.CSSStyleRule):
                            selector_text = inner_rule.selectorText
                            line = self._get_line_number(css_content, inner_rule.selectorText, str(css_file))
                            
                            # Extract class selectors
                            class_matches = re.findall(r'\.([a-zA-Z0-9_-]+)', selector_text)
                            for match in class_matches:
                                if match not in self.excluded_selectors:
                                    selector = f".{match}"
                                    selectors[selector].append({
                                        'file': str(Path(css_file).resolve()),
                                        'line': line
                                    })
                            
                            # Extract ID selectors
                            id_matches = re.findall(r'#([a-zA-Z0-9_-]+)', selector_text)
                            for match in id_matches:
                                if match not in self.excluded_selectors:
                                    selector = f"#{match}"
                                    selectors[selector].append({
                                        'file': str(Path(css_file).resolve()),
                                        'line': line
                                    })
        
        return dict(selectors)
    
    def _find_used_selectors(self, source_files: List[Path], css_selectors: Set[str]) -> Set[str]:
        """Find which CSS selectors are actually used in source files."""
        used_selectors = set()
        
        for source_file in source_files:
            try:
                with open(source_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Check each selector
                for selector in css_selectors:
                    selector_name = selector[1:]  # Remove . or #
                    
                    if selector.startswith('.'):
                        # Check for class usage
                        if self._find_class_usage(content, selector_name):
                            used_selectors.add(selector)
                    elif selector.startswith('#'):
                        # Check for ID usage
                        if self._find_id_usage(content, selector_name):
                            used_selectors.add(selector)
            
            except Exception as e:
                self.errors.append(f"Error reading {source_file}: {str(e)}")
        
        return used_selectors
    
    def _find_class_usage(self, content: str, class_name: str) -> bool:
        """Check if a class is used in the content."""
        # Look for class attribute containing the class name (case-insensitive)
        # This is a simple heuristic that searches within a tag's attributes.
        pattern = rf'\bclass\b[^>]*\b{re.escape(class_name)}\b'
        return bool(re.search(pattern, content, flags=re.IGNORECASE))
    
    def _find_id_usage(self, content: str, id_name: str) -> bool:
        """Check if an ID is used in the content."""
        # Look for id attribute containing the id name (case-insensitive)
        pattern = rf'\bid\b[^>]*\b{re.escape(id_name)}\b'
        return bool(re.search(pattern, content, flags=re.IGNORECASE))
    
    def analyze(self, css_files: List[Path], source_files: List[Path], page_map: Dict[str, Any] = None, per_page_unused: bool = False, skip_unreferenced: bool = False) -> Dict[str, Any]:
        """Analyze for unused CSS selectors."""
        results = {
            'unused_selectors': {},
            'used_selectors': set(),
            'total_selectors': 0,
            'usage_percentage': 0,
            'errors': []
        }
        if page_map:
            # Accept either full parse_html_for_css result or just pages dict
            if 'pages' in page_map:
                pages = page_map.get('pages', {})
                results['unused_files'] = page_map.get('unreferenced_css', [])
            else:
                pages = page_map
                results['unused_files'] = []
        else:
            pages = None
        
        # Optionally filter css_files to only those referenced by pages
        if pages and skip_unreferenced:
            referenced: Set[str] = set()
            for _, info in pages.items():
                for p in info.get('css_chain', []) or []:
                    referenced.add(str(Path(p).resolve()))
            css_files = [Path(p).resolve() for p in css_files if str(Path(p).resolve()) in referenced]
        
        # Extract all CSS selectors with locations
        css_selectors = self._extract_css_selectors(css_files)
        results['total_selectors'] = len(css_selectors)
        
        if not css_selectors:
            return results
        
        # Map selector -> set(files where defined)
        selector_def_files: Dict[str, Set[str]] = {sel: set(loc['file'] for loc in locs) for sel, locs in css_selectors.items()}

        # Find used selectors (site-wide)
        used_sitewide = self._find_used_selectors(source_files, set(css_selectors.keys()))

        # If pages are known, restrict usage to pages that actually include a CSS file where the selector is defined
        if pages:
            used_page_scoped: Set[str] = set()
            # Build page -> set(css files included)
            page_css_map: Dict[str, Set[str]] = {pg: set(info.get('css_chain', [])) for pg, info in pages.items()}
            for sel in used_sitewide:
                def_files = selector_def_files.get(sel, set())
                # If any page both uses selector and includes any defining CSS file, count as used
                # We don't have per-page usage content, so keep sitewide used but only if any page includes
                if any(def_files & page_css_map.get(pg, set()) for pg in page_css_map.keys()):
                    used_page_scoped.add(sel)
            results['used_selectors'] = used_page_scoped
        else:
            results['used_selectors'] = used_sitewide
        
        # Calculate unused selectors with locations
        unused_selectors = {k: v for k, v in css_selectors.items() if k not in results['used_selectors']}
        results['unused_selectors'] = unused_selectors
        
        # Calculate usage percentage
        if css_selectors:
            results['usage_percentage'] = (len(results['used_selectors']) / len(css_selectors)) * 100
        
        results['errors'] = self.errors
        
        return results

class StructureAnalyzer(BaseAnalyzer):
    """Analyzer for CSS structure, prefixes, and patterns."""
    
    def __init__(self):
        super().__init__()
        # Prefix separators to consider inside class/id names (BEM-style and common patterns)
        # We treat one or more '-' or '_' as a separator boundary.
        self._prefix_splitter = re.compile(r'[-_]+')
    
    def analyze(self, css_files: List[Path], page_map: Dict[str, Any] = None, skip_unreferenced: bool = False) -> Dict[str, Any]:
        """Analyze CSS structure for prefixes, comments, and patterns.

        If page_map is provided and skip_unreferenced is True, only analyze CSS files
        referenced by any page's css_chain. When page_map is provided, include a
        'load_order' section mirroring per-page CSS chains for consistency.
        """
        # Normalize pages mapping if provided
        pages = None
        if page_map:
            if isinstance(page_map, dict) and 'pages' in page_map:
                pages = page_map.get('pages') or {}
            else:
                pages = page_map

        # Optionally filter css_files to only those referenced by pages
        if pages and skip_unreferenced:
            referenced: Set[str] = set()
            for _, info in pages.items():
                for p in info.get('css_chain', []) or []:
                    referenced.add(str(Path(p).resolve()))
            css_files = [Path(p).resolve() for p in css_files if str(Path(p).resolve()) in referenced]

        # Ensure paths are Path objects
        css_files = [Path(p).resolve() for p in css_files]

        # Analyze
        results = {
            'comments': [],
            'prefixes': defaultdict(int),
            'prefix_groups': defaultdict(list),
            'selector_counts': defaultdict(int),
            'total_rules': 0,
            'total_comments': 0,
            'errors': []
        }
        
        for css_file in css_files:
            stylesheet, css_content = self._parse_css_file(css_file)
            if not stylesheet:
                continue
            
            for rule in stylesheet:
                if isinstance(rule, cssutils.css.CSSStyleRule):
                    # Analyze selector structure
                    selector_text = rule.selectorText
                    results['selector_counts'][selector_text] += 1
                    results['total_rules'] += 1
                    
                    # Extract and analyze prefixes
                    self._analyze_prefixes(selector_text, results)
                
                elif isinstance(rule, cssutils.css.CSSMediaRule):
                    # Analyze media query rules
                    for inner_rule in rule:
                        if isinstance(inner_rule, cssutils.css.CSSStyleRule):
                            selector_text = inner_rule.selectorText
                            results['selector_counts'][selector_text] += 1
                            results['total_rules'] += 1
                            
                            # Extract and analyze prefixes
                            self._analyze_prefixes(selector_text, results)
                
                elif isinstance(rule, cssutils.css.CSSComment):
                    # Collect comments with correct line number
                    line = self._get_line_number(css_content, rule.cssText, str(css_file))
                    comment_info = {
                        'text': rule.cssText,
                        'file': str(Path(css_file).resolve()),
                        'line': line
                    }
                    results['comments'].append(comment_info)
                    results['total_comments'] += 1
        
        # Attach load order (per page) and analyzed files for reporter context
        if pages:
            results['load_order'] = {page: (info.get('css_chain', []) or []) for page, info in pages.items() if info.get('css_chain')}
        results['analyzed_files'] = [str(Path(p).resolve()) for p in css_files]

        results['errors'] = self.errors
        return results

    def _analyze_prefixes(self, selector_text: str, results: Dict[str, Any]):
        """Analyze prefixes in selector text for both classes and IDs.

        Advanced prefix detection:
        - For names containing '-' or '_' (including multiple or mixed in a row),
          record hierarchical prefixes at each boundary, e.g.,
          "note_highlight_bg" -> ["note", "note_highlight"],
          "nt-note-item" -> ["nt", "nt_note"]. Mixed or repeated separators are treated
          as a single boundary and normalized with '_'.
        - If no separators are present, fall back to camelCase/PascalCase tokenization and
          record cumulative prefixes across word chunks, e.g.,
          "HeaderListItem" -> ["header", "header_list"], "headerHelper" -> ["header"].
        - Numeric suffixes are handled via tokenization: e.g., "body1" -> ["body"].
        """
        # Extract class and id names
        class_matches = re.findall(r'\.([a-zA-Z0-9_-]+)', selector_text)
        id_matches = re.findall(r'#([a-zA-Z0-9_-]+)', selector_text)

        def record(name: str, kind: str):
            prefixes_to_add: list[str] = []
            # Prefer separator-based hierarchical prefixes
            if '-' in name or '_' in name:
                all_parts = [p for p in self._prefix_splitter.split(name) if p]
                if len(all_parts) >= 2:
                    # Build cumulative prefixes up to n-1 parts; normalize separator as '_'
                    for i in range(1, len(all_parts)):
                        prefixes_to_add.append("_".join(all_parts[:i]))
            else:
                # Camel/PascalCase tokenization (includes numeric chunks)
                chunks = re.findall(r'[A-Z]?[a-z]+|[A-Z]+(?![a-z])|[0-9]+', name)
                # Need at least two chunks; build cumulative prefixes up to n-1
                if len(chunks) >= 2:
                    chunks_lower = [c.lower() for c in chunks]
                    for i in range(1, len(chunks_lower)):
                        prefixes_to_add.append("_".join(chunks_lower[:i]))

            if not prefixes_to_add:
                return

            label = f".{name}" if kind == 'class' else f"#{name}"
            # Deduplicate within this token to avoid double counting same prefix (edge cases)
            seen_local: set[str] = set()
            for p in prefixes_to_add:
                norm_prefix = p.lower()
                if not norm_prefix or norm_prefix in seen_local:
                    continue
                seen_local.add(norm_prefix)
                results['prefixes'][norm_prefix] += 1
                results['prefix_groups'][norm_prefix].append(label)

        for cname in class_matches:
            record(cname, 'class')
        for iname in id_matches:
            record(iname, 'id')
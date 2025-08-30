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
    
    def analyze(self, css_files: List[Path]) -> Dict[str, Any]:
        """Analyze CSS files for duplicates."""
        results = {
            'selectors': defaultdict(list),
            'media_queries': defaultdict(list),
            'comments': defaultdict(list),
            'errors': []
        }
        
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
                        results['selectors'][selector].append({
                            'file': str(css_file),
                            'line': line
                        })
                
                elif isinstance(rule, cssutils.css.CSSMediaRule):
                    # Handle media queries
                    media_query = rule.media.mediaText
                    if media_query:
                        line = self._get_line_number(css_content, "@media " + rule.media.mediaText, str(css_file))
                        results['media_queries'][media_query].append({
                            'file': str(css_file),
                            'line': line
                        })
                    
                    # Also check rules within media queries
                    for inner_rule in rule:
                        if isinstance(inner_rule, cssutils.css.CSSStyleRule):
                            selector = inner_rule.selectorText
                            if selector:
                                line = self._get_line_number(css_content, inner_rule.selectorText, str(css_file))
                                results['selectors'][selector].append({
                                    'file': str(css_file),
                                    'line': line
                                })
                
                elif isinstance(rule, cssutils.css.CSSComment):
                    # Handle comments
                    comment = rule.cssText
                    if comment and comment.strip():
                        line = self._get_line_number(css_content, rule.cssText, str(css_file))
                        results['comments'][comment].append({
                            'file': str(css_file),
                            'line': line
                        })
        
        # Filter to keep only duplicates
        results['selectors'] = {k: v for k, v in results['selectors'].items() if len(v) > 1}
        results['media_queries'] = {k: v for k, v in results['media_queries'].items() if len(v) > 1}
        results['comments'] = {k: v for k, v in results['comments'].items() if len(v) > 1}
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
    
    def _extract_css_selectors(self, css_files: List[Path]) -> Set[str]:
        """Extract all unique CSS selectors from CSS files."""
        selectors = set()
        
        for css_file in css_files:
            stylesheet, css_content = self._parse_css_file(css_file)
            if not stylesheet:
                continue
            
            for rule in stylesheet:
                if isinstance(rule, cssutils.css.CSSStyleRule):
                    # Parse selector text to extract individual class and ID names
                    selector_text = rule.selectorText
                    
                    # Extract class selectors
                    class_matches = re.findall(r'\.([a-zA-Z0-9_-]+)', selector_text)
                    for match in class_matches:
                        if match not in self.excluded_selectors:
                            selectors.add(f".{match}")
                    
                    # Extract ID selectors
                    id_matches = re.findall(r'#([a-zA-Z0-9_-]+)', selector_text)
                    for match in id_matches:
                        if match not in self.excluded_selectors:
                            selectors.add(f"#{match}")
                
                elif isinstance(rule, cssutils.css.CSSMediaRule):
                    # Check rules within media queries
                    for inner_rule in rule:
                        if isinstance(inner_rule, cssutils.css.CSSStyleRule):
                            selector_text = inner_rule.selectorText
                            
                            # Extract class selectors
                            class_matches = re.findall(r'\.([a-zA-Z0-9_-]+)', selector_text)
                            for match in class_matches:
                                if match not in self.excluded_selectors:
                                    selectors.add(f".{match}")
                            
                            # Extract ID selectors
                            id_matches = re.findall(r'#([a-zA-Z0-9_-]+)', selector_text)
                            for match in id_matches:
                                if match not in self.excluded_selectors:
                                    selectors.add(f"#{match}")
        
        return selectors
    
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
        # Look for class="..." containing the class name
        pattern = rf'class\s*=\s*["\'][^"\']*?\b{re.escape(class_name)}\b'
        return bool(re.search(pattern, content))
    
    def _find_id_usage(self, content: str, id_name: str) -> bool:
        """Check if an ID is used in the content."""
        # Look for id="..." containing the ID name
        pattern = rf'id\s*=\s*["\'][^"\']*?\b{re.escape(id_name)}\b'
        return bool(re.search(pattern, content))
    
    def analyze(self, css_files: List[Path], source_files: List[Path]) -> Dict[str, Any]:
        """Analyze for unused CSS selectors."""
        results = {
            'unused_selectors': set(),
            'used_selectors': set(),
            'total_selectors': 0,
            'usage_percentage': 0,
            'errors': []
        }
        
        # Extract all CSS selectors
        css_selectors = self._extract_css_selectors(css_files)
        results['total_selectors'] = len(css_selectors)
        
        if not css_selectors:
            return results
        
        # Find used selectors
        used_selectors = self._find_used_selectors(source_files, css_selectors)
        results['used_selectors'] = used_selectors
        
        # Calculate unused selectors
        unused_selectors = css_selectors - used_selectors
        results['unused_selectors'] = unused_selectors
        
        # Calculate usage percentage
        if css_selectors:
            results['usage_percentage'] = (len(used_selectors) / len(css_selectors)) * 100
        
        results['errors'] = self.errors
        
        return results

class StructureAnalyzer(BaseAnalyzer):
    """Analyzer for CSS structure, prefixes, and patterns."""
    
    def __init__(self):
        super().__init__()
        self.prefix_pattern = re.compile(r'\.([a-zA-Z0-9_-]+)-')
    
    def analyze(self, css_files: List[Path]) -> Dict[str, Any]:
        """Analyze CSS structure for prefixes, comments, and patterns."""
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
                        'file': str(css_file),
                        'line': line
                    }
                    results['comments'].append(comment_info)
                    results['total_comments'] += 1
        
        results['errors'] = self.errors
        return results
    
    def _analyze_prefixes(self, selector_text: str, results: Dict[str, Any]):
        """Analyze class prefixes in selector text."""
        # Extract class names
        class_matches = re.findall(r'\.([a-zA-Z0-9_-]+)', selector_text)
        
        for class_name in class_matches:
            # Find prefix (everything before the last hyphen)
            prefix_match = self.prefix_pattern.match(f".{class_name}")
            if prefix_match:
                prefix = prefix_match.group(1)
                results['prefixes'][prefix] += 1
                results['prefix_groups'][prefix].append(class_name)
# CSS Analyzer - Usage Summary

## Quick Start

The CSS Analyzer is now ready to use! Here's how to get started:

### Installation

1. Navigate to the css_analyser directory:
```bash
cd /home/z/my-project/css_analyser
```

2. Install dependencies (if not already installed):
```bash
pip install --break-system-packages -r requirements.txt
```

### Basic Usage

#### 1. Analyze Duplicates
Find duplicate CSS selectors, media queries, and comments:

```bash
# Analyze a specific CSS file
python -m main duplicates ./sample_project/style.css

# Analyze a whole project directory
python -m main duplicates ./sample_project/

# Generate HTML report
python -m main duplicates ./sample_project/ --output-html duplicates_report.html

# Merge duplicates honoring load order (global)
python -m main duplicates ./sample_project/ --merge --page-root ./sample_project/

# Merge per page (when load order differs across pages)
python -m main duplicates ./sample_project/ --merge --per-page-merge --page-root ./sample_project/
```

#### 2. Find Unused Selectors
Identify unused CSS selectors by scanning HTML, PHP, and JS files:

```bash
# Find unused selectors in a project
python -m main unused ./sample_project/

# Generate HTML report
python -m main unused ./sample_project/ --output-html unused_report.html

# Page-aware unused detection and unused CSS files
python -m main unused ./sample_project/ --page-root ./sample_project/
```

#### 3. Analyze Structure
Analyze CSS structure for prefixes, comments, and patterns:

```bash
# Analyze CSS structure
python -m main structure ./sample_project/

# Generate HTML report
python -m main structure ./sample_project/ --output-html structure_report.html
```

#### 4. Comprehensive Analysis
Run all analyses at once:

```bash
# Run comprehensive analysis
python -m main analyze ./sample_project/

# Generate comprehensive HTML report
python -m main analyze ./sample_project/ --output-html comprehensive_report.html
```

### Example Output

The tool provides both console output and HTML reports:

#### Console Output Example:
```
╭─────────────────────────────────╮
│ Unused Selector Analysis Report │
╰─────────────────────────────────╯
          Summary           
┏━━━━━━━━━━━━━━━━━━┳━━━━━━━┓
┃ Metric           ┃ Count ┃
┡━━━━━━━━━━━━━━━━━━╇━━━━━━━┩
│ Total Selectors  │ 19    │
│ Used Selectors   │ 13    │
│ Unused Selectors │ 6     │
│ Usage Percentage │ 68.4% │
└──────────────────┴───────┘
```

#### HTML Report Features:
- Professional styling with responsive design
- Summary statistics with visual indicators
- Detailed tables with sorting and filtering
- Color-coded results (green for good, yellow for warnings, red for issues)
- Interactive and mobile-friendly layout

### Sample Files

The analyzer comes with sample files in `./sample_project/`:
- `style.css` - Sample CSS with various selectors and patterns
- `index.html` - Sample HTML using some CSS classes
- `script.js` - Sample JavaScript with dynamic class creation
- `index.php` - Sample PHP with more complex HTML structure

### Supported File Types

**CSS Files:**
- `.css` - Standard CSS files
- `.scss` - Sass files
- `.sass` - Sass files
- `.less` - Less files

**Source Files (for unused selector detection):**
- `.html`, `.htm` - HTML files
- `.php` - PHP files
- `.js`, `.jsx` - JavaScript files
- `.ts`, `.tsx` - TypeScript files
- `.vue` - Vue.js files

### Excluded Directories

By default, these directories are excluded from analysis:
- `node_modules`, `vendor`
- `.git`, `.svn`, `.hg`
- `.idea`, `.vscode`
- `build`, `dist`, `out`
- `coverage`, `__pycache__`
- `venv`, `env`, `.env`

### Features at a Glance

✅ **Duplicate Detection**
- Duplicate CSS selectors
- Duplicate media queries
- Duplicate comments
- Location tracking with file paths and line numbers

✅ **Unused Selector Analysis**
- Comprehensive CSS selector extraction
- HTML/PHP/JS file scanning
- Smart regex-based detection
- Usage statistics and percentages

✅ **Structure Analysis**
- Class prefix analysis and grouping
- Comment cataloging
- CSS rule counting
- Pattern recognition

✅ **Reporting**
- Rich console output with colors and tables
- Professional HTML reports
- Responsive design for mobile devices
- Comprehensive and individual analysis reports

### Tips for Best Results

1. **Run on Complete Projects**: For unused selector analysis, ensure all relevant HTML, PHP, and JS files are included
2. **Use HTML Reports**: HTML reports provide better visualization and are easier to share
3. **Check Exclusions**: Verify that excluded directories don't contain relevant files
4. **Review Carefully**: Some "unused" selectors might be used dynamically in JavaScript

### Troubleshooting

If you encounter any issues:
1. Ensure all dependencies are installed
2. Check file permissions
3. Verify that CSS files are valid
4. Look for any error messages in the console output

The CSS Analyzer is now ready to help you optimize your CSS codebase!
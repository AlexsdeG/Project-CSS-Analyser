# CSS Analyzer

A comprehensive CLI tool for analyzing CSS and web project files. CSS Analyzer helps you identify duplicate selectors, unused CSS, and structural patterns in your CSS codebase.

## Features

- **Duplicate Analysis**: Find duplicate CSS selectors, media queries, and comments
- **Merged CSS Generation**: Generate merged CSS rules for duplicate selectors with proper cascading
- **Unused Selector Detection**: Identify unused CSS selectors by scanning HTML, PHP, and JS files
- **Structure Analysis**: Analyze CSS structure for prefixes, comments, and patterns
- **Multiple Output Formats**: Rich console output and detailed HTML reports
- **Comprehensive Analysis**: Run all analyses at once with a single command

## Installation

### From Source

1. Clone the repository:
```bash
git clone https://github.com/your-username/css-analyzer.git
cd css-analyzer
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Install the package:
```bash
pip install -e .
```

### Using pip (when published)

```bash
pip install css-analyzer
```

## Usage

CSS Analyzer provides several commands for different types of analysis:

### Basic Commands

#### Analyze Duplicates

Find duplicate CSS selectors, media queries, and comments:

```bash
# Analyze duplicates in a specific CSS file
css-analyzer duplicates ./path/to/style.css

# Analyze duplicates in a project directory
css-analyzer duplicates ./path/to/project/

# Generate HTML report
css-analyzer duplicates ./path/to/project/ --output-html report.html

# Enable verbose output
css-analyzer duplicates ./path/to/project/ --verbose
```

#### Find Unused Selectors

Identify unused CSS selectors by scanning HTML, PHP, and JS files:

```bash
# Find unused selectors in a project
css-analyzer unused ./path/to/project/

# Generate merged CSS rules for duplicates:
python -m main duplicates ./path/to/project --merge

# Generate HTML report
css-analyzer unused ./path/to/project/ --output-html unused-report.html

# Enable verbose output
css-analyzer unused ./path/to/project/ --verbose
```

#### Analyze Structure

Analyze CSS structure for prefixes, comments, and patterns:

```bash
# Analyze CSS structure
css-analyzer structure ./path/to/project/

# Generate HTML report
css-analyzer structure ./path/to/project/ --output-html structure-report.html

# Enable verbose output
css-analyzer structure ./path/to/project/ --verbose
```

#### Comprehensive Analysis

Run all analyses at once:

```bash
# Run comprehensive analysis
css-analyzer analyze ./path/to/project/

# Generate comprehensive HTML report
css-analyzer analyze ./path/to/project/ --output-html comprehensive-report.html

# Enable verbose output
css-analyzer analyze ./path/to/project/ --verbose
```

### Command Line Options

All commands support the following options:

- `--merge`: Generate merged CSS rules for duplicate selectors
- `--output-html PATH`: Generate an HTML report at the specified path
- `--verbose, -v`: Enable verbose output for debugging

## File Support

### CSS Files

The analyzer supports the following CSS file extensions:
- `.css`
- `.scss`
- `.sass`
- `.less`

### Source Files

For unused selector detection, the analyzer scans these file types:
- `.html`, `.htm`
- `.php`
- `.js`, `.jsx`
- `.ts`, `.tsx`
- `.vue`

### Excluded Directories

By default, the following directories are excluded from analysis:
- `node_modules`
- `vendor`
- `.git`, `.svn`, `.hg`
- `.idea`, `.vscode`
- `build`, `dist`, `out`
- `coverage`
- `__pycache__`, `.pytest_cache`
- `venv`, `env`, `.env`
- `.tox`

## Report Examples

### Console Output

The console output uses the `rich` library to provide formatted, color-coded reports:

```
╭──────────────────────────────────────────────────────────────╮
│                    Duplicate CSS Analysis Report              │
╰──────────────────────────────────────────────────────────────╯

Duplicate Selectors
┌─────────────────────────┬───────┬─────────────────────────┐
│ Selector                │ Count │ Locations               │
├─────────────────────────┼───────┼─────────────────────────┤
│ .mdt-container         │ 3     │ style.css:25            │
│                         │       │ theme.css:120           │
│                         │       │ custom.css:45           │
└─────────────────────────┴───────┴─────────────────────────┘
```

### HTML Reports

HTML reports provide detailed, interactive analysis with:
- Summary statistics
- Detailed tables with sorting and filtering
- Color-coded results
- Responsive design for mobile devices

## Examples

### Example 1: Basic Duplicate Analysis

```bash
css-analyzer duplicates ./assets/css/
```

This will analyze all CSS files in the `./assets/css/` directory and display duplicate findings in the console.

### Example 2: Unused Selector Analysis with HTML Report

```bash
css-analyzer unused ./my-project/ --output-html unused-report.html
```

This will scan your project for unused CSS selectors and generate a detailed HTML report.

### Example 3: Comprehensive Analysis

```bash
css-analyzer analyze ./my-project/ --output-html full-report.html --verbose
```

This will run all analyses (duplicates, unused selectors, structure) and generate a comprehensive HTML report with verbose logging.

## How It Works

### Duplicate Analysis

1. **CSS Parsing**: Uses `cssutils` to parse CSS files and extract selectors, media queries, and comments
2. **Duplicate Detection**: Identifies identical items across files
3. **Location Tracking**: Records file paths and line numbers for each duplicate
4. **Reporting**: Generates reports showing duplicates and their locations

### Unused Selector Detection

1. **CSS Selector Extraction**: Extracts all class and ID selectors from CSS files
2. **Source File Scanning**: Scans HTML, PHP, and JS files for selector usage
3. **Usage Detection**: Uses regex patterns to find selectors in `class` and `id` attributes
4. **Comparison**: Compares CSS selectors against found usage to identify unused selectors

### Structure Analysis

1. **Prefix Analysis**: Extracts and analyzes class prefixes (e.g., `mdt-` from `.mdt-container`)
2. **Comment Analysis**: Catalogs all CSS comments with their locations
3. **Pattern Detection**: Identifies structural patterns and naming conventions
4. **Statistics**: Provides counts and metrics for CSS structure

## Limitations

- **Dynamic Selectors**: Cannot detect selectors that are dynamically generated in JavaScript
- **Framework Classes**: Some framework/utility classes are excluded by default but may be used dynamically
- **Complex Selectors**: Very complex CSS selectors may not be accurately parsed
- **Encoding Issues**: Some files with unusual encodings may not be read correctly

## Development

### Setting Up Development Environment

1. Clone the repository:
```bash
git clone https://github.com/your-username/css-analyzer.git
cd css-analyzer
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
pip install -e .
```

### Running Tests

```bash
python -m pytest tests/
```

### Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

If you encounter any issues or have questions:

1. Check the [Issues](https://github.com/your-username/css-analyzer/issues) page
2. Create a new issue with detailed information about your problem
3. Include sample CSS files and expected behavior when possible

## Changelog

### Version 1.0.0

- Initial release
- Duplicate CSS analysis
- Unused selector detection
- Structure analysis
- Console and HTML reporting
- Support for multiple CSS file formats
- Comprehensive project analysis
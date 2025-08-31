"""
Reporting modules for CSS Analyzer.
"""

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from pathlib import Path
from typing import Dict, List, Any, Set
import json
from jinja2 import Template

class ConsoleReporter:
    """Handles console reporting using rich library."""
    
    def __init__(self):
        self.console = Console()
    
    def report_duplicates(self, results: Dict[str, Any], merge: bool = False):
        """Report duplicate analysis results."""
        self.console.print(Panel.fit("[bold blue]Duplicate CSS Analysis Report[/bold blue]"))
        
        # Report duplicate selectors
        if results['selectors']:
            self.console.print("\n[bold red]Duplicate Selectors:[/bold red]")
            selector_table = Table(title="Duplicate CSS Selectors")
            selector_table.add_column("Selector", style="cyan")
            selector_table.add_column("Count", style="magenta")
            selector_table.add_column("Locations", style="yellow")
            
            for selector, locations in results['selectors'].items():
                count = len(locations)
                locations_str = "\n".join([f"{loc['file']}:{loc['line']}" for loc in locations])
                selector_table.add_row(selector, str(count), locations_str)
            
            self.console.print(selector_table)
        else:
            self.console.print("[green]✓ No duplicate selectors found.[/green]")
        
        # Report duplicate media queries
        if results['media_queries']:
            self.console.print("\n[bold red]Duplicate Media Queries:[/bold red]")
            media_table = Table(title="Duplicate Media Queries")
            media_table.add_column("Media Query", style="cyan")
            media_table.add_column("Count", style="magenta")
            media_table.add_column("Locations", style="yellow")
            
            for media_query, locations in results['media_queries'].items():
                count = len(locations)
                locations_str = "\n".join([f"{loc['file']}:{loc['line']}" for loc in locations])
                media_table.add_row(media_query, str(count), locations_str)
            
            self.console.print(media_table)
        else:
            self.console.print("[green]✓ No duplicate media queries found.[/green]")
        
        # Report duplicate comments
        if results['comments']:
            self.console.print("\n[bold red]Duplicate Comments:[/bold red]")
            comment_table = Table(title="Duplicate Comments")
            comment_table.add_column("Comment", style="cyan")
            comment_table.add_column("Count", style="magenta")
            comment_table.add_column("Locations", style="yellow")
            
            for comment, locations in results['comments'].items():
                count = len(locations)
                locations_str = "\n".join([f"{loc['file']}:{loc['line']}" for loc in locations])
                comment_table.add_row(comment, str(count), locations_str)
            
            self.console.print(comment_table)
        else:
            self.console.print("[green]✓ No duplicate comments found.[/green]")
        
        # Load order per page
        if results.get('load_order'):
            self.console.print("\n[bold blue]Load Order (per page):[/bold blue]")
            for page, chain in results['load_order'].items():
                table = Table(title=str(page))
                table.add_column("Index", justify="right")
                table.add_column("CSS File", overflow="fold")
                for idx, item in enumerate(chain[:20]):  # show top N
                    table.add_row(str(idx + 1), item)
                if len(chain) > 20:
                    table.add_row("…", f"(+{len(chain)-20} more)")
                self.console.print(table)

        # Conflicts
        if results.get('warnings'):
            self.console.print("\n[bold yellow]Conflicts & Overrides:[/bold yellow]")
            warn_table = Table(title="Conflicts & Overrides")
            warn_table.add_column("Selector", style="cyan")
            warn_table.add_column("Property", style="magenta")
            warn_table.add_column("Page", style="green")
            warn_table.add_column("From", style="yellow")
            warn_table.add_column("To", style="yellow")
            warn_table.add_column("Reason", style="white")
            for w in results['warnings']:
                warn_table.add_row(
                    w.get('selector', ''),
                    w.get('property', ''),
                    str(w.get('page', '—')),
                    w.get('from', ''),
                    w.get('to', ''),
                    w.get('reason', w.get('type', ''))
                )
            self.console.print(warn_table)

        # Report merged CSS if available
        if merge and 'merged' in results and results['merged']:
            self.console.print("\n[bold green]Merged CSS Rules:[/bold green]")
            for selector, merged_css in results['merged'].items():
                self.console.print(f"[cyan]{merged_css}[/cyan]")
                self.console.print()

        # Per-page merged CSS
        if merge and 'merged_per_page' in results and results['merged_per_page']:
            self.console.print("\n[bold green]Merged CSS Rules (Per Page):[/bold green]")
            for page, selmap in results['merged_per_page'].items():
                self.console.print(f"[bold]{page}[/bold]")
                for selector, merged_css in selmap.items():
                    self.console.print(f"[cyan]{merged_css}[/cyan]")
                    self.console.print()
        
        # Report errors
        if results['errors']:
            self.console.print("\n[bold red]Errors:[/bold red]")
            for error in results['errors']:
                self.console.print(f"- {error}")
    
    def report_unused_selectors(self, results: Dict[str, Any]):
        """Report unused selector analysis results."""
        self.console.print(Panel.fit("[bold blue]Unused Selector Analysis Report[/bold blue]"))
        
        total_selectors = results['total_selectors']
        used_selectors = len(results['used_selectors'])
        unused_selectors = len(results['unused_selectors'])
        usage_percentage = results['usage_percentage']
        
        # Summary
        summary_table = Table(title="Summary")
        summary_table.add_column("Metric", style="cyan")
        summary_table.add_column("Count", style="magenta")
        
        summary_table.add_row("Total Selectors", str(total_selectors))
        summary_table.add_row("Used Selectors", str(used_selectors))
        summary_table.add_row("Unused Selectors", str(unused_selectors))
        summary_table.add_row("Usage Percentage", f"{usage_percentage:.1f}%")
        
        self.console.print(summary_table)
        
        # Unused CSS files
        if results.get('unused_files'):
            self.console.print("\n[bold yellow]Unused CSS Files:[/bold yellow]")
            file_table = Table()
            file_table.add_column("File", style="cyan")
            for f in results['unused_files']:
                file_table.add_row(f)
            self.console.print(file_table)

        # Unused selectors
        if results['unused_selectors']:
            self.console.print(f"\n[bold red]Unused Selectors ({unused_selectors}):[/bold red]")
            
            # Create a table with unused selectors
            unused_table = Table()
            unused_table.add_column("Selector", style="cyan")
            unused_table.add_column("File", style="yellow")
            unused_table.add_column("Line", style="magenta")
            
            for selector, locations in results['unused_selectors'].items():
                for location in locations:
                    unused_table.add_row(selector, location['file'], str(location['line']))
            
            self.console.print(unused_table)
        else:
            self.console.print("[green]✓ No unused selectors found.[/green]")
        
        # Report errors
        if results['errors']:
            self.console.print("\n[bold red]Errors:[/bold red]")
            for error in results['errors']:
                self.console.print(f"- {error}")
    
    def report_structure(self, results: Dict[str, Any]):
        """Report structure analysis results."""
        self.console.print(Panel.fit("[bold blue]CSS Structure Analysis Report[/bold blue]"))
        
        # Summary
        summary_table = Table(title="Summary")
        summary_table.add_column("Metric", style="cyan")
        summary_table.add_column("Count", style="magenta")
        
        summary_table.add_row("Total CSS Rules", str(results['total_rules']))
        summary_table.add_row("Total Comments", str(results['total_comments']))
        summary_table.add_row("Unique Prefixes", str(len(results['prefixes'])))
        
        self.console.print(summary_table)
        
        # Prefix analysis
        if results['prefixes']:
            self.console.print("\n[bold blue]Class Prefix Analysis:[/bold blue]")
            prefix_table = Table(title="Class Prefixes")
            prefix_table.add_column("Prefix", style="cyan")
            prefix_table.add_column("Count", style="magenta")
            prefix_table.add_column("Example Classes", style="yellow")
            
            # Sort prefixes by count (descending)
            sorted_prefixes = sorted(results['prefixes'].items(), key=lambda x: x[1], reverse=True)
            
            for prefix, count in sorted_prefixes[:10]:  # Show top 10
                classes = results['prefix_groups'][prefix]
                example_classes = ", ".join(classes[:3])  # Show first 3 examples
                if len(classes) > 3:
                    example_classes += f" (+{len(classes) - 3} more)"
                prefix_table.add_row(prefix, str(count), example_classes)
            
            self.console.print(prefix_table)
        
        # Comments
        if results['comments']:
            self.console.print(f"\n[bold blue]CSS Comments ({len(results['comments'])}):[/bold blue]")
            comments_table = Table(title="CSS Comments")
            comments_table.add_column("File", style="cyan")
            comments_table.add_column("Line", style="magenta")
            comments_table.add_column("Comment", style="yellow")
            
            # Show first 10 comments
            for comment in results['comments'][:10]:
                comment_text = comment['text'][:80] + "..." if len(comment['text']) > 80 else comment['text']
                comments_table.add_row(
                    Path(comment['file']).name,
                    str(comment['line']),
                    comment_text
                )
            
            self.console.print(comments_table)
            
            if len(results['comments']) > 10:
                self.console.print(f"[yellow]... and {len(results['comments']) - 10} more comments[/yellow]")
        
        # Report errors
        if results['errors']:
            self.console.print("\n[bold red]Errors:[/bold red]")
            for error in results['errors']:
                self.console.print(f"[red]• {error}[/red]")
    
    def report_comprehensive(self, all_results: Dict[str, Any]):
        """Report comprehensive analysis results."""
        self.console.print(Panel.fit("[bold blue]Comprehensive CSS Analysis Report[/bold blue]"))
        
        # Duplicates section
        self.console.print("\n[bold cyan]1. Duplicate Analysis[/bold cyan]")
        if 'duplicates' in all_results:
            self._report_duplicates_summary(all_results['duplicates'])
        
        # Unused selectors section
        self.console.print("\n[bold cyan]2. Unused Selector Analysis[/bold cyan]")
        if 'unused' in all_results:
            self._report_unused_summary(all_results['unused'])
        
        # Structure section
        self.console.print("\n[bold cyan]3. Structure Analysis[/bold cyan]")
        if 'structure' in all_results:
            self._report_structure_summary(all_results['structure'])
    
    def _report_duplicates_summary(self, results: Dict[str, Any]):
        """Report a summary of duplicate analysis."""
        dup_selectors = len(results['selectors'])
        dup_media = len(results['media_queries'])
        dup_comments = len(results['comments'])
        
        if dup_selectors + dup_media + dup_comments > 0:
            self.console.print(f"[red]Found {dup_selectors} duplicate selectors, {dup_media} duplicate media queries, and {dup_comments} duplicate comments.[/red]")
        else:
            self.console.print("[green]✓ No duplicates found.[/green]")
    
    def _report_unused_summary(self, results: Dict[str, Any]):
        """Report a summary of unused selector analysis."""
        unused_count = len(results['unused_selectors'])
        usage_percentage = results['usage_percentage']
        
        if unused_count > 0:
            self.console.print(f"[red]Found {unused_count} unused selectors ({usage_percentage:.1f}% usage rate).[/red]")
        else:
            self.console.print("[green]✓ No unused selectors found.[/green]")
    
    def _report_structure_summary(self, results: Dict[str, Any]):
        """Report a summary of structure analysis."""
        total_rules = results['total_rules']
        total_comments = results['total_comments']
        unique_prefixes = len(results['prefixes'])
        
        self.console.print(f"[blue]Analyzed {total_rules} CSS rules with {total_comments} comments and {unique_prefixes} unique prefixes.[/blue]")

class HTMLReporter:
    """Handles HTML report generation."""
    
    def __init__(self):
        self.template = self._load_template()
    
    def _ensure_reports_folder(self):
        """Ensure the reports folder exists."""
        reports_dir = Path("reports")
        reports_dir.mkdir(exist_ok=True)
    
    def _load_template(self) -> Template:
        """Load the HTML template."""
        template_path = Path(__file__).parent / "templates" / "report_template.html"
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                return Template(f.read())
        except FileNotFoundError:
            # Fallback to basic template
            return self._get_fallback_template()
    
    def _get_fallback_template(self) -> Template:
        """Get a basic fallback template."""
        return Template("""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CSS Analysis Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #333; border-bottom: 2px solid #007bff; padding-bottom: 10px; }
        h2 { color: #555; margin-top: 30px; }
        .summary { background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0; }
        .error { color: #dc3545; background: #f8d7da; padding: 10px; border-radius: 5px; margin: 10px 0; }
        .success { color: #155724; background: #d4edda; padding: 10px; border-radius: 5px; margin: 10px 0; }
        table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }
        th { background-color: #f2f2f2; font-weight: bold; }
        tr:nth-child(even) { background-color: #f9f9f9; }
        .code { font-family: monospace; background: #f1f1f1; padding: 2px 4px; border-radius: 3px; }
        .badge { display: inline-block; padding: 4px 8px; border-radius: 12px; font-size: 12px; font-weight: bold; }
        .badge-danger { background-color: #dc3545; color: white; }
        .badge-warning { background-color: #ffc107; color: #212529; }
        .badge-info { background-color: #17a2b8; color: white; }
        .badge-success { background-color: #28a745; color: white; }
    </style>
</head>
<body>
    <div class="container">
        <h1>CSS Analysis Report</h1>
        
        {% if analysis_type == 'duplicates' %}
            {{ duplicates_section(results, merge) }}
        {% elif analysis_type == 'unused' %}
            {{ unused_section(results) }}
        {% elif analysis_type == 'structure' %}
            {{ structure_section(results) }}
        {% endif %}
    </div>
</body>
</html>
        """)
    
    def generate_report(self, results: Dict[str, Any], output_path: Path, analysis_type: str, merge: bool = False):
        """Generate HTML report for a specific analysis type."""
        self._ensure_reports_folder()
        
        # Prefix output_path with reports/ if it's relative and not already under reports/
        if not output_path.is_absolute():
            op_str = str(output_path).replace('\\', '/').lstrip('./')
            if not op_str.startswith('reports/'):
                output_path = Path("reports") / output_path
            
        html_content = self.template.render(
            results=results,
            analysis_type=analysis_type,
            merge=merge,
            duplicates_section=self._duplicates_section,
            unused_section=self._unused_section,
            structure_section=self._structure_section
        )
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
    
    def generate_comprehensive_report(self, all_results: Dict[str, Any], output_path: Path):
        """Generate comprehensive HTML report."""
        self._ensure_reports_folder()
        
        # Prefix output_path with reports/ if it's relative and not already under reports/
        if not output_path.is_absolute():
            op_str = str(output_path).replace('\\', '/').lstrip('./')
            if not op_str.startswith('reports/'):
                output_path = Path("reports") / output_path
            
        html_content = self._get_comprehensive_template().render(
            all_results=all_results,
            duplicates_section=self._duplicates_section,
            unused_section=self._unused_section,
            structure_section=self._structure_section
        )
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
    
    def _get_comprehensive_template(self) -> Template:
        """Get comprehensive report template."""
        return Template("""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Comprehensive CSS Analysis Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #333; border-bottom: 2px solid #007bff; padding-bottom: 10px; }
        h2 { color: #555; margin-top: 30px; }
        h3 { color: #666; margin-top: 25px; }
        .summary { background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0; }
        .error { color: #dc3545; background: #f8d7da; padding: 10px; border-radius: 5px; margin: 10px 0; }
        .success { color: #155724; background: #d4edda; padding: 10px; border-radius: 5px; margin: 10px 0; }
        table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }
        th { background-color: #f2f2f2; font-weight: bold; }
        tr:nth-child(even) { background-color: #f9f9f9; }
        .code { font-family: monospace; background: #f1f1f1; padding: 2px 4px; border-radius: 3px; }
        .badge { display: inline-block; padding: 4px 8px; border-radius: 12px; font-size: 12px; font-weight: bold; }
        .badge-danger { background-color: #dc3545; color: white; }
        .badge-warning { background-color: #ffc107; color: #212529; }
        .badge-info { background-color: #17a2b8; color: white; }
        .badge-success { background-color: #28a745; color: white; }
        .section { margin: 30px 0; padding: 20px; border: 1px solid #e0e0e0; border-radius: 8px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Comprehensive CSS Analysis Report</h1>
        
        <div class="section">
            <h2>1. Duplicate Analysis</h2>
            {{ duplicates_section(all_results.get('duplicates', {}), 'merged' in all_results.get('duplicates', {})) }}
        </div>
        
        <div class="section">
            <h2>2. Unused Selector Analysis</h2>
            {{ unused_section(all_results.get('unused', {})) }}
        </div>
        
        <div class="section">
            <h2>3. Structure Analysis</h2>
            {{ structure_section(all_results.get('structure', {})) }}
        </div>
    </div>
</body>
</html>
        """)
    
    def _duplicates_section(self, results: Dict[str, Any], merge: bool = False) -> str:
        """Generate HTML for duplicates section."""
        html = []
        
        if not results or not any(results.get(key) for key in ['selectors', 'media_queries', 'comments']):
            html.append('<div class="success">✓ No duplicates found.</div>')
            return ''.join(html)
        
        # Duplicate selectors
        if results.get('selectors'):
            html.append('<h3>Duplicate Selectors</h3>')
            html.append('<table>')
            html.append('<tr><th>Selector</th><th>Count</th><th>Locations</th></tr>')
            
            for selector, locations in results['selectors'].items():
                count = len(locations)
                locations_str = '<br>'.join([f"{loc['file']}:{loc['line']}" for loc in locations])
                html.append(f'<tr><td>{selector}</td><td>{count}</td><td>{locations_str}</td></tr>')
            
            html.append('</table>')
        
        # Duplicate media queries
        if results.get('media_queries'):
            html.append('<h3>Duplicate Media Queries</h3>')
            html.append('<table>')
            html.append('<tr><th>Media Query</th><th>Count</th><th>Locations</th></tr>')
            
            for media_query, locations in results['media_queries'].items():
                count = len(locations)
                locations_str = '<br>'.join([f"{loc['file']}:{loc['line']}" for loc in locations])
                html.append(f'<tr><td>{media_query}</td><td>{count}</td><td>{locations_str}</td></tr>')
            
            html.append('</table>')
        
        # Duplicate comments
        if results.get('comments'):
            html.append('<h3>Duplicate Comments</h3>')
            html.append('<table>')
            html.append('<tr><th>Comment</th><th>Count</th><th>Locations</th></tr>')
            
            for comment, locations in results['comments'].items():
                count = len(locations)
                locations_str = '<br>'.join([f"{loc['file']}:{loc['line']}" for loc in locations])
                html.append(f'<tr><td>{comment}</td><td>{count}</td><td>{locations_str}</td></tr>')
            
            html.append('</table>')
        
        # Load order section
        if results.get('load_order'):
            html.append('<h3>Load Order (per page)</h3>')
            for page, chain in results['load_order'].items():
                html.append(f'<h4>{page}</h4>')
                html.append('<table>')
                html.append('<tr><th>#</th><th>CSS File</th></tr>')
                for i, item in enumerate(chain):
                    html.append(f'<tr><td>{i+1}</td><td>{item}</td></tr>')
                html.append('</table>')

        # Conflicts & Overrides
        if results.get('warnings'):
            html.append('<h3>Conflicts & Overrides</h3>')
            html.append('<table>')
            html.append('<tr><th>Selector</th><th>Property</th><th>Page</th><th>From</th><th>To</th><th>Reason</th></tr>')
            badge_map = {
                'important-blocks-normal': 'badge badge-danger',
                'important-vs-important': 'badge badge-warning',
                'later-overrides-earlier': 'badge badge-info'
            }
            for w in results['warnings']:
                reason = w.get('reason', w.get('type',''))
                cls = badge_map.get(w.get('type',''), 'badge')
                html.append(f"<tr><td>{w.get('selector','')}</td><td>{w.get('property','')}</td><td>{w.get('page','')}</td><td>{w.get('from','')}</td><td>{w.get('to','')}</td><td><span class='{cls}'>{reason}</span></td></tr>")
            html.append('</table>')
            html.append('<p><small>Legend: <span class="badge badge-danger">important blocks normal</span> <span class="badge badge-warning">important vs important</span> <span class="badge badge-info">later overrides earlier</span></small></p>')

        # Merged CSS
        if merge and 'merged' in results and results['merged']:
            html.append('<h3>Merged CSS Rules</h3><br>')
            for selector, merged_css in results['merged'].items():
                html.append(f'<pre><code>{merged_css}</code></pre><br>')
        if merge and 'merged_per_page' in results and results['merged_per_page']:
            html.append('<h3>Merged CSS Rules (Per Page)</h3>')
            for page, selmap in results['merged_per_page'].items():
                html.append(f'<h4>{page}</h4>')
                for selector, merged_css in selmap.items():
                    html.append(f'<pre><code>{merged_css}</code></pre>')
        
        return ''.join(html)
    
    def _unused_section(self, results: Dict[str, Any]) -> str:
        """Generate HTML for unused selectors section."""
        html = []
        
        if not results:
            html.append('<div class="error">No data available.</div>')
            return ''.join(html)
        
        # Summary
        html.append('<div class="summary">')
        html.append('<h3>Summary</h3>')
        html.append('<table>')
        html.append('<tr><th>Metric</th><th>Count</th></tr>')
        html.append(f'<tr><td>Total Selectors</td><td>{results.get("total_selectors", 0)}</td></tr>')
        html.append(f'<tr><td>Used Selectors</td><td>{len(results.get("used_selectors", set()))}</td></tr>')
        html.append(f'<tr><td>Unused Selectors</td><td>{len(results.get("unused_selectors", {}))}</td></tr>')
        html.append(f'<tr><td>Usage Percentage</td><td>{results.get("usage_percentage", 0):.1f}%</td></tr>')
        html.append('</table>')
        html.append('</div>')
        
        # Unused CSS files
        if results.get('unused_files'):
            html.append('<h3>Unused CSS Files</h3>')
            html.append('<table>')
            html.append('<tr><th>File</th></tr>')
            for f in results['unused_files']:
                html.append(f'<tr><td>{f}</td></tr>')
            html.append('</table>')

        # Unused selectors
        if results.get('unused_selectors'):
            html.append('<h3>Unused Selectors</h3>')
            html.append('<table>')
            html.append('<tr><th>Selector</th><th>File</th><th>Line</th></tr>')
            
            for selector, locations in results['unused_selectors'].items():
                for location in locations:
                    html.append(f'<tr><td>{selector}</td><td>{location["file"]}</td><td>{location["line"]}</td></tr>')
            
            html.append('</table>')
        else:
            html.append('<div class="success">✓ No unused selectors found.</div>')
        
        return ''.join(html)
    
    def _structure_section(self, results: Dict[str, Any]) -> str:
        """Generate HTML for structure section."""
        html = []
        
        if not results:
            html.append('<div class="error">No analysis results available.</div>')
            return ''.join(html)
        
        # Summary
        html.append('<div class="summary">')
        html.append('<h3>Summary</h3>')
        html.append('<table>')
        html.append('<tr><th>Metric</th><th>Count</th></tr>')
        html.append(f'<tr><td>Total CSS Rules</td><td>{results.get("total_rules", 0)}</td></tr>')
        html.append(f'<tr><td>Total Comments</td><td>{results.get("total_comments", 0)}</td></tr>')
        html.append(f'<tr><td>Unique Prefixes</td><td>{len(results.get("prefixes", {}))}</td></tr>')
        html.append('</table>')
        html.append('</div>')
        
        # Prefix analysis
        if results.get('prefixes'):
            html.append('<h3>Class Prefix Analysis</h3>')
            html.append('<table>')
            html.append('<tr><th>Prefix</th><th>Count</th><th>Example Classes</th></tr>')
            
            sorted_prefixes = sorted(results['prefixes'].items(), key=lambda x: x[1], reverse=True)
            
            for prefix, count in sorted_prefixes[:10]:  # Show top 10
                classes = results['prefix_groups'][prefix]
                example_classes = ", ".join(classes[:3])
                if len(classes) > 3:
                    example_classes += f" (+{len(classes) - 3} more)"
                html.append(f'<tr><td><code>{prefix}</code></td><td>{count}</td><td>{example_classes}</td></tr>')
            
            html.append('</table>')
        
        # Comments
        if results.get('comments'):
            html.append(f'<h3>CSS Comments ({len(results["comments"])})</h3>')
            html.append('<table>')
            html.append('<tr><th>File</th><th>Line</th><th>Comment</th></tr>')
            
            for comment in results['comments'][:10]:  # Show first 10
                comment_text = comment['text'][:80] + "..." if len(comment['text']) > 80 else comment['text']
                html.append(f'<tr><td>{comment["file"]}</td><td>{comment["line"]}</td><td><code>{comment_text}</code></td></tr>')
            
            html.append('</table>')
            
            if len(results['comments']) > 10:
                html.append(f'<p>... and {len(results["comments"]) - 10} more comments</p>')
        
        return ''.join(html)
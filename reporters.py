"""
Reporting modules for CSS Analyzer.
"""

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from pathlib import Path
from typing import Dict, List, Any
from jinja2 import Template
from utils import (
    make_file_href,
    make_rel_label,
    make_console_link_text,
    make_html_link,
    DEFAULT_TABLE_CAP,
    make_vscode_href,
)


class ConsoleReporter:
    """Handles console reporting using rich library."""

    def __init__(self, project_root: Path = None, full: bool = False, use_vscode: bool = False):
        self.console = Console()
        self.project_root = Path(project_root).resolve() if project_root else None
        self.full = full
        self.table_cap = None if full else DEFAULT_TABLE_CAP
        self.use_vscode = use_vscode

    def _link_cell(self, path_str: str) -> str:
        """Render a rich-styled clickable link for a file path."""
        try:
            p = Path(path_str).resolve()
        except Exception:
            return path_str
        label = make_rel_label(p, self.project_root or p.parent)
        href = make_vscode_href(p) if self.use_vscode else make_file_href(p)
        text, style = make_console_link_text(label, href)
        return f"[{style}]{text}[/]"

    def _format_file_line(self, value: str) -> str:
        """Convert a 'file:line' string into a linkified version preserving the line number.

        Handles Windows drive letters by splitting on the last colon.
        """
        if not isinstance(value, str) or ":" not in value:
            return self._link_cell(value)

        idx = value.rfind(":")
        maybe_line = value[idx + 1 :]
        file_part = value[:idx]

        # If the tail isn't a pure integer, just link the whole thing as a file path
        if not maybe_line.isdigit():
            return self._link_cell(value)

        try:
            p = Path(file_part).resolve()
        except Exception:
            return value

        # Label like \relative\path.css:123
        label = make_rel_label(p, self.project_root or p.parent) + f":{maybe_line}"

        # If VS Code deep links are enabled, make a vscode:// link to jump to the line.
        # Otherwise, keep a normal file link and show the line as text.
        if self.use_vscode:
            href = make_vscode_href(p, int(maybe_line))
            text, style = make_console_link_text(label, href)
            return f"[{style}]{text}[/]"
        else:
            return f"{self._link_cell(str(p))}:{maybe_line}"

    def _maybe_cap(self, seq: List[Any]) -> List[Any]:
        if self.full or self.table_cap is None:
            return seq
        return seq[: self.table_cap]

    def report_duplicates(self, results: Dict[str, Any], merge: bool = False):
        """Report duplicate analysis results."""
        self.console.print(Panel.fit("[bold blue]Duplicate CSS Analysis Report[/bold blue]"))

        # Duplicate selectors
        selectors = results.get("selectors", {})
        if selectors:
            self.console.print("\n[bold red]Duplicate Selectors:[/bold red]")
            selector_table = Table(title="Duplicate CSS Selectors")
            selector_table.add_column("Selector", style="cyan")
            selector_table.add_column("Count", style="magenta")
            selector_table.add_column("Locations", style="yellow")

            items = list(selectors.items())
            shown = self._maybe_cap(items)
            for selector, locations in shown:
                count = len(locations)
                if self.use_vscode:
                    locations_str = "\n".join(
                        [self._format_file_line(f"{loc['file']}:{loc['line']}") for loc in locations]
                    )
                else:
                    locations_str = "\n".join(
                        [f"{self._link_cell(loc['file'])}:{loc['line']}" for loc in locations]
                    )
                selector_table.add_row(selector, str(count), locations_str)

            self.console.print(selector_table)
            if not self.full and len(items) > len(shown):
                self.console.print(
                    f"[yellow]Showing {len(shown)} of {len(items)} selectors. Use --full to show all.[/yellow]"
                )
        else:
            self.console.print("[green]✓ No duplicate selectors found.[/green]")

        # Duplicate media queries
        media = results.get("media_queries", {})
        if media:
            self.console.print("\n[bold red]Duplicate Media Queries:[/bold red]")
            media_table = Table(title="Duplicate Media Queries")
            media_table.add_column("Media Query", style="cyan")
            media_table.add_column("Count", style="magenta")
            media_table.add_column("Locations", style="yellow")

            items = list(media.items())
            shown = self._maybe_cap(items)
            for mq, locations in shown:
                count = len(locations)
                if self.use_vscode:
                    locations_str = "\n".join(
                        [self._format_file_line(f"{loc['file']}:{loc['line']}") for loc in locations]
                    )
                else:
                    locations_str = "\n".join(
                        [f"{self._link_cell(loc['file'])}:{loc['line']}" for loc in locations]
                    )
                media_table.add_row(mq, str(count), locations_str)

            self.console.print(media_table)
            if not self.full and len(items) > len(shown):
                self.console.print(
                    f"[yellow]Showing {len(shown)} of {len(items)} media queries. Use --full to show all.[/yellow]"
                )
        else:
            self.console.print("[green]✓ No duplicate media queries found.[/green]")

        # Duplicate comments
        comments = results.get("comments", {})
        if comments:
            self.console.print("\n[bold red]Duplicate Comments:[/bold red]")
            comment_table = Table(title="Duplicate Comments")
            comment_table.add_column("Comment", style="cyan")
            comment_table.add_column("Count", style="magenta")
            comment_table.add_column("Locations", style="yellow")

            items = list(comments.items())
            shown = self._maybe_cap(items)
            for comment, locations in shown:
                count = len(locations)
                if self.use_vscode:
                    locations_str = "\n".join(
                        [self._format_file_line(f"{loc['file']}:{loc['line']}") for loc in locations]
                    )
                else:
                    locations_str = "\n".join(
                        [f"{self._link_cell(loc['file'])}:{loc['line']}" for loc in locations]
                    )
                comment_table.add_row(comment, str(count), locations_str)

            self.console.print(comment_table)
            if not self.full and len(items) > len(shown):
                self.console.print(
                    f"[yellow]Showing {len(shown)} of {len(items)} comments. Use --full to show all.[/yellow]"
                )
        else:
            self.console.print("[green]✓ No duplicate comments found.[/green]")

        # Load order per page
        if "load_order" in results:
            load_order = results.get("load_order") or {}
            non_empty = {pg: ch for pg, ch in load_order.items() if ch}
            self.console.print("\n[bold blue]Load Order (per page):[/bold blue]")
            if non_empty:
                for page, chain in non_empty.items():
                    table = Table(title=str(page))
                    table.add_column("Index", justify="right")
                    table.add_column("CSS File", overflow="fold")
                    show_chain = chain if self.full else chain[: (self.table_cap or DEFAULT_TABLE_CAP)]
                    for idx, item in enumerate(show_chain):
                        table.add_row(str(idx + 1), self._link_cell(item))
                    if not self.full and len(chain) > len(show_chain):
                        table.add_row("…", f"(+{len(chain) - len(show_chain)} more)")
                    self.console.print(table)
            else:
                self.console.print("[yellow]No load order detected.[/yellow]")

        # Conflicts
        if results.get("warnings"):
            self.console.print("\n[bold yellow]Conflicts & Overrides:[/bold yellow]")
            warn_table = Table(title="Conflicts & Overrides")
            warn_table.add_column("Selector", style="cyan")
            warn_table.add_column("Property", style="magenta")
            warn_table.add_column("Page", style="green")
            warn_table.add_column("From", style="yellow")
            warn_table.add_column("To", style="yellow")
            warn_table.add_column("Reason", style="white")
            warns = results["warnings"]
            shown = self._maybe_cap(warns)
            for w in shown:
                from_val = self._format_file_line(w.get("from", ""))
                to_val = self._format_file_line(w.get("to", ""))
                warn_table.add_row(
                    w.get("selector", ""),
                    w.get("property", ""),
                    str(w.get("page", "—")),
                    from_val,
                    to_val,
                    w.get("reason", w.get("type", "")),
                )
            self.console.print(warn_table)
            if not self.full and len(warns) > len(shown):
                self.console.print(
                    f"[yellow]Showing {len(shown)} of {len(warns)} warnings. Use --full to show all.[/yellow]"
                )

        # Merged CSS
        if merge and results.get("merged"):
            self.console.print("\n[bold green]Merged CSS Rules:[/bold green]")
            for selector, merged_css in results["merged"].items():
                self.console.print(f"[cyan]{merged_css}[/cyan]")
                self.console.print()

        if merge and results.get("merged_per_page"):
            self.console.print("\n[bold green]Merged CSS Rules (Per Page):[/bold green]")
            for page, selmap in results["merged_per_page"].items():
                self.console.print(f"[bold]{page}[/bold]")
                for selector, merged_css in selmap.items():
                    self.console.print(f"[cyan]{merged_css}[/cyan]")

        # Errors
        if results.get("errors"):
            self.console.print("\n[bold red]Errors:[/bold red]")
            for error in results["errors"]:
                self.console.print(f"- {error}")

    def report_unused_selectors(self, results: Dict[str, Any]):
        """Report unused selector analysis results."""
        self.console.print(Panel.fit("[bold blue]Unused Selector Analysis Report[/bold blue]"))

        total_selectors = results.get("total_selectors", 0)
        used_selectors = len(results.get("used_selectors", set()))
        unused_selectors_count = len(results.get("unused_selectors", {}))
        usage_percentage = results.get("usage_percentage", 0)

        summary_table = Table(title="Summary")
        summary_table.add_column("Metric", style="cyan")
        summary_table.add_column("Count", style="magenta")
        summary_table.add_row("Total Selectors", str(total_selectors))
        summary_table.add_row("Used Selectors", str(used_selectors))
        summary_table.add_row("Unused Selectors", str(unused_selectors_count))
        summary_table.add_row("Usage Percentage", f"{usage_percentage:.1f}%")
        self.console.print(summary_table)

        # Unused CSS files (from page map if available)
        if results.get("unused_files"):
            file_table = Table(title="Unused CSS Files")
            file_table.add_column("File", style="yellow")
            files = list(results["unused_files"]) or []
            shown = self._maybe_cap(files)
            for f in shown:
                file_table.add_row(self._link_cell(f))
            self.console.print(file_table)
            if not self.full and len(files) > len(shown):
                self.console.print(
                    f"[yellow]Showing {len(shown)} of {len(files)} files. Use --full to show all.[/yellow]"
                )

        # Unused selectors
        unused = results.get("unused_selectors", {})
        if unused:
            self.console.print(
                f"\n[bold red]Unused Selectors ({unused_selectors_count}):[/bold red]"
            )
            unused_table = Table()
            unused_table.add_column("Selector", style="cyan")
            unused_table.add_column("File", style="yellow")
            unused_table.add_column("Line", style="magenta")

            # Flatten entries for possible capping
            rows: List[Any] = []
            for selector, locations in unused.items():
                for loc in locations:
                    rows.append((selector, loc.get("file", ""), loc.get("line", "")))
            shown = self._maybe_cap(rows)
            for selector, file_path, line in shown:
                file_cell = (
                    self._format_file_line(f"{file_path}:{line}")
                    if self.use_vscode and str(line).isdigit()
                    else self._link_cell(file_path)
                )
                unused_table.add_row(selector, file_cell, str(line))
            self.console.print(unused_table)
            if not self.full and len(rows) > len(shown):
                self.console.print(
                    f"[yellow]Showing {len(shown)} of {len(rows)} occurrences. Use --full to show all.[/yellow]"
                )
        else:
            self.console.print("[green]✓ No unused selectors found.[/green]")

        # Errors
        if results.get("errors"):
            self.console.print("\n[bold red]Errors:[/bold red]")
            for error in results["errors"]:
                self.console.print(f"- {error}")

    def report_structure(self, results: Dict[str, Any]):
        """Report structure analysis results."""
        self.console.print(Panel.fit("[bold blue]Structure Analysis Report[/bold blue]"))

        total_rules = results.get("total_rules", 0)
        total_comments = results.get("total_comments", 0)
        unique_prefixes = len(results.get("prefixes", {}))

        summary_table = Table(title="Summary")
        summary_table.add_column("Metric", style="cyan")
        summary_table.add_column("Count", style="magenta")
        summary_table.add_row("Total CSS Rules", str(total_rules))
        summary_table.add_row("Total Comments", str(total_comments))
        summary_table.add_row("Unique Prefixes", str(unique_prefixes))
        self.console.print(summary_table)

        # Load order per page (if provided by analyzer)
        if "load_order" in results:
            load_order = results.get("load_order") or {}
            non_empty = {pg: ch for pg, ch in load_order.items() if ch}
            self.console.print("\n[bold blue]Load Order (per page):[/bold blue]")
            if non_empty:
                for page, chain in non_empty.items():
                    table = Table(title=str(page))
                    table.add_column("Index", justify="right")
                    table.add_column("CSS File", overflow="fold")
                    show_chain = chain if self.full else chain[: (self.table_cap or DEFAULT_TABLE_CAP)]
                    for idx, item in enumerate(show_chain):
                        table.add_row(str(idx + 1), self._link_cell(item))
                    if not self.full and len(chain) > len(show_chain):
                        table.add_row("…", f"(+{len(chain) - len(show_chain)} more)")
                    self.console.print(table)
            else:
                self.console.print("[yellow]No load order detected.[/yellow]")

        # Prefix analysis
        prefixes = results.get("prefixes", {})
        filtered = [(k, v) for k, v in prefixes.items() if v >= 2]
        if filtered:
            self.console.print("\n[bold blue]Prefix Analysis (classes and IDs):[/bold blue]")
            prefix_table = Table(title="Prefixes")
            prefix_table.add_column("Prefix", style="cyan")
            prefix_table.add_column("Count", style="magenta")
            prefix_table.add_column("Example Tokens", style="yellow")
            sorted_prefixes = sorted(filtered, key=lambda x: x[1], reverse=True)
            shown = sorted_prefixes if self.full else sorted_prefixes[: (self.table_cap or DEFAULT_TABLE_CAP)]
            for prefix, count in shown:
                classes = results.get("prefix_groups", {}).get(prefix, [])
                if self.full:
                    example_classes = ", ".join(classes)
                else:
                    example_classes = ", ".join(classes[:3])
                    if len(classes) > 3:
                        example_classes += f" (+{len(classes) - 3} more)"
                prefix_table.add_row(prefix, str(count), example_classes)
            self.console.print(prefix_table)
            if not self.full and len(sorted_prefixes) > len(shown):
                self.console.print(
                    f"[yellow]Showing {len(shown)} of {len(sorted_prefixes)} prefixes (count ≥ 2). Use --full to show all.[/yellow]"
                )

        # Comments
        comments_list = results.get("comments", [])
        if comments_list:
            self.console.print(
                f"\n[bold blue]CSS Comments ({len(comments_list)}):[/bold blue]"
            )
            comments_table = Table(title="CSS Comments")
            comments_table.add_column("File", style="cyan")
            comments_table.add_column("Line", style="magenta")
            comments_table.add_column("Comment", style="yellow")

            shown = self._maybe_cap(comments_list)
            for comment in shown:
                if self.full:
                    comment_text = comment.get("text", "")
                else:
                    comment_text = (
                        (comment.get("text", "")[:80] + "...")
                        if len(comment.get("text", "")) > 80
                        else comment.get("text", "")
                    )
                file_cell = (
                    self._format_file_line(f"{comment.get('file','')}:{comment.get('line','')}")
                    if self.use_vscode and str(comment.get("line", "")).isdigit()
                    else self._link_cell(comment.get("file", ""))
                )
                comments_table.add_row(
                    file_cell,
                    str(comment.get("line", "")),
                    comment_text,
                )
            self.console.print(comments_table)
            if not self.full and len(comments_list) > len(shown):
                self.console.print(
                    f"[yellow]Showing {len(shown)} of {len(comments_list)} comments. Use --full to show all.[/yellow]"
                )

        # Errors
        if results.get("errors"):
            self.console.print("\n[bold red]Errors:[/bold red]")
            for error in results["errors"]:
                self.console.print(f"[red]• {error}[/red]")

    def report_comprehensive(self, all_results: Dict[str, Any]):
        """Report comprehensive analysis results."""
        self.console.print(Panel.fit("[bold blue]Comprehensive CSS Analysis Report[/bold blue]"))

        # Duplicates section
        self.console.print("\n[bold cyan]1. Duplicate Analysis[/bold cyan]")
        if "duplicates" in all_results:
            self._report_duplicates_summary(all_results["duplicates"])

        # Unused selectors section
        self.console.print("\n[bold cyan]2. Unused Selector Analysis[/bold cyan]")
        if "unused" in all_results:
            self._report_unused_summary(all_results["unused"])

        # Structure section
        self.console.print("\n[bold cyan]3. Structure Analysis[/bold cyan]")
        if "structure" in all_results:
            self._report_structure_summary(all_results["structure"])

    def _report_duplicates_summary(self, results: Dict[str, Any]):
        """Report a summary of duplicate analysis."""
        dup_selectors = len(results.get("selectors", {}))
        dup_media = len(results.get("media_queries", {}))
        dup_comments = len(results.get("comments", {}))

        if dup_selectors + dup_media + dup_comments > 0:
            self.console.print(
                f"[red]Found {dup_selectors} duplicate selectors, {dup_media} duplicate media queries, and {dup_comments} duplicate comments.[/red]"
            )
        else:
            self.console.print("[green]✓ No duplicates found.[/green]")

    def _report_unused_summary(self, results: Dict[str, Any]):
        """Report a summary of unused selector analysis."""
        unused_count = len(results.get("unused_selectors", {}))
        usage_percentage = results.get("usage_percentage", 0)

        if unused_count > 0:
            self.console.print(
                f"[red]Found {unused_count} unused selectors ({usage_percentage:.1f}% usage rate).[/red]"
            )
        else:
            self.console.print("[green]✓ No unused selectors found.[/green]")

    def _report_structure_summary(self, results: Dict[str, Any]):
        """Report a summary of structure analysis."""
        total_rules = results.get("total_rules", 0)
        total_comments = results.get("total_comments", 0)
        unique_prefixes = len(results.get("prefixes", {}))

        self.console.print(
            f"[blue]Analyzed {total_rules} CSS rules with {total_comments} comments and {unique_prefixes} unique prefixes.[/blue]"
        )


class HTMLReporter:
    """Handles HTML report generation."""

    def __init__(self, project_root: Path = None, full: bool = False, use_vscode: bool = False):
        self.template = self._load_template()
        self.project_root = Path(project_root).resolve() if project_root else None
        self.full = full
        self.table_cap = None if full else DEFAULT_TABLE_CAP
        self.use_vscode = use_vscode

    def _ensure_reports_folder(self):
        """Ensure the reports folder exists."""
        reports_dir = Path("reports")
        reports_dir.mkdir(exist_ok=True)

    def _load_template(self) -> Template:
        """Load the HTML template."""
        template_path = Path(__file__).parent / "templates" / "report_template.html"
        try:
            with open(template_path, "r", encoding="utf-8") as f:
                return Template(f.read())
        except FileNotFoundError:
            # Fallback to basic template
            return self._get_fallback_template()

    def _get_fallback_template(self) -> Template:
        """Get a basic fallback template."""
        return Template(
            """
<!DOCTYPE html>
<html lang=\"en\">
<head>
    <meta charset=\"UTF-8\">
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
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
        a.file-link { color: #c59f00; text-decoration: underline; }
    </style>
</head>
<body>
    <div class=\"container\">
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
        """
        )

    def _make_link(self, path_str: str) -> str:
        try:
            p = Path(path_str).resolve()
        except Exception:
            return path_str
        label = make_rel_label(p, self.project_root or p.parent)
        href = make_vscode_href(p) if self.use_vscode else make_file_href(p)
        return make_html_link(label, href)

    def _format_file_line_html(self, value: str) -> str:
        """Format 'file:line' into an HTML link that can jump to the line in VS Code."""
        if not isinstance(value, str) or ":" not in value:
            return self._make_link(value)

        idx = value.rfind(":")
        maybe_line = value[idx + 1 :]
        file_part = value[:idx]

        try:
            p = Path(file_part).resolve()
        except Exception:
            return value

        label = make_rel_label(p, self.project_root or p.parent) + (f":{maybe_line}" if maybe_line.isdigit() else "")
        if self.use_vscode and maybe_line.isdigit():
            href = make_vscode_href(p, int(maybe_line))
            return make_html_link(label, href)
        else:
            # Fallback to plain file link; preserve visible ":line" text in label
            href = make_file_href(p)
            return make_html_link(label, href)

    def _maybe_cap(self, seq: List[Any]) -> List[Any]:
        if self.full or self.table_cap is None:
            return seq
        return seq[: self.table_cap]

    def generate_report(self, results: Dict[str, Any], output_path: Path, analysis_type: str, merge: bool = False):
        """Generate HTML report for a specific analysis type."""
        self._ensure_reports_folder()

        # Prefix output_path with reports/ if it's relative and not already under reports/
        if not output_path.is_absolute():
            op_str = str(output_path).replace("\\", "/").lstrip("./")
            if not op_str.startswith("reports/"):
                output_path = Path("reports") / output_path

        html_content = self.template.render(
            results=results,
            analysis_type=analysis_type,
            merge=merge,
            duplicates_section=self._duplicates_section,
            unused_section=self._unused_section,
            structure_section=self._structure_section,
        )

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)

    def generate_comprehensive_report(self, all_results: Dict[str, Any], output_path: Path):
        """Generate comprehensive HTML report."""
        self._ensure_reports_folder()

        # Prefix output_path with reports/ if it's relative and not already under reports/
        if not output_path.is_absolute():
            op_str = str(output_path).replace("\\", "/").lstrip("./")
            if not op_str.startswith("reports/"):
                output_path = Path("reports") / output_path

        html_content = self._get_comprehensive_template().render(
            all_results=all_results,
            duplicates_section=self._duplicates_section,
            unused_section=self._unused_section,
            structure_section=self._structure_section,
        )

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)

    def _get_comprehensive_template(self) -> Template:
        """Get comprehensive report template."""
        return Template(
            """
<!DOCTYPE html>
<html lang=\"en\">
<head>
    <meta charset=\"UTF-8\">
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
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
        a.file-link { color: #c59f00; text-decoration: underline; }
        .section { margin: 30px 0; padding: 20px; border: 1px solid #e0e0e0; border-radius: 8px; }
    </style>
</head>
<body>
    <div class=\"container\">
        <h1>Comprehensive CSS Analysis Report</h1>
        
        <div class=\"section\">
            <h2>1. Duplicate Analysis</h2>
            {{ duplicates_section(all_results.get('duplicates', {}), 'merged' in all_results.get('duplicates', {})) }}
        </div>
        
        <div class=\"section\">
            <h2>2. Unused Selector Analysis</h2>
            {{ unused_section(all_results.get('unused', {})) }}
        </div>
        
        <div class=\"section\">
            <h2>3. Structure Analysis</h2>
            {{ structure_section(all_results.get('structure', {})) }}
        </div>
    </div>
</body>
</html>
        """
        )

    def _duplicates_section(self, results: Dict[str, Any], merge: bool = False) -> str:
        """Generate HTML for duplicates section."""
        html: List[str] = []

        if not results or not any(results.get(key) for key in ["selectors", "media_queries", "comments", "warnings", "load_order"]):
            html.append('<div class="success">✓ No duplicates found.</div>')
            return "".join(html)

        # Duplicate selectors
        selectors = results.get("selectors", {})
        if selectors:
            html.append("<h3>Duplicate Selectors</h3>")
            html.append("<table>")
            html.append("<tr><th>Selector</th><th>Count</th><th>Locations</th></tr>")
            items = list(selectors.items())
            shown = self._maybe_cap(items)
            for selector, locations in shown:
                count = len(locations)
                if self.use_vscode:
                    locs = [self._format_file_line_html(f"{loc['file']}:{loc['line']}") for loc in locations]
                else:
                    locs = [f"{self._make_link(loc['file'])}:{loc['line']}" for loc in locations]
                locations_str = "<br>".join(locs)
                html.append(f"<tr><td>{selector}</td><td>{count}</td><td>{locations_str}</td></tr>")
            html.append("</table>")
            if not self.full and len(items) > len(shown):
                html.append(
                    f"<p><em>Showing {len(shown)} of {len(items)} selectors. Use --full to show all.</em></p>"
                )

        # Duplicate media queries
        media = results.get("media_queries", {})
        if media:
            html.append("<h3>Duplicate Media Queries</h3>")
            html.append("<table>")
            html.append("<tr><th>Media Query</th><th>Count</th><th>Locations</th></tr>")
            items = list(media.items())
            shown = self._maybe_cap(items)
            for mq, locations in shown:
                count = len(locations)
                if self.use_vscode:
                    locs = [self._format_file_line_html(f"{loc['file']}:{loc['line']}") for loc in locations]
                else:
                    locs = [f"{self._make_link(loc['file'])}:{loc['line']}" for loc in locations]
                locations_str = "<br>".join(locs)
                html.append(f"<tr><td>{mq}</td><td>{count}</td><td>{locations_str}</td></tr>")
            html.append("</table>")
            if not self.full and len(items) > len(shown):
                html.append(
                    f"<p><em>Showing {len(shown)} of {len(items)} media queries. Use --full to show all.</em></p>"
                )

        # Duplicate comments
        comments = results.get("comments", {})
        if comments:
            html.append("<h3>Duplicate Comments</h3>")
            html.append("<table>")
            html.append("<tr><th>Comment</th><th>Count</th><th>Locations</th></tr>")
            items = list(comments.items())
            shown = self._maybe_cap(items)
            for comment, locations in shown:
                count = len(locations)
                if self.use_vscode:
                    locs = [self._format_file_line_html(f"{loc['file']}:{loc['line']}") for loc in locations]
                else:
                    locs = [f"{self._make_link(loc['file'])}:{loc['line']}" for loc in locations]
                locations_str = "<br>".join(locs)
                html.append(f"<tr><td>{comment}</td><td>{count}</td><td>{locations_str}</td></tr>")
            html.append("</table>")
            if not self.full and len(items) > len(shown):
                html.append(
                    f"<p><em>Showing {len(shown)} of {len(items)} comments. Use --full to show all.</em></p>"
                )

        # Load order section
        if "load_order" in results:
            load_order = results.get("load_order") or {}
            non_empty = {pg: ch for pg, ch in load_order.items() if ch}
            html.append("<h3>Load Order (per page)</h3>")
            if non_empty:
                for page, chain in non_empty.items():
                    html.append(f"<h4>{page}</h4>")
                    html.append("<table>")
                    html.append("<tr><th>#</th><th>CSS File</th></tr>")
                    show_chain = chain if self.full else chain[: (self.table_cap or DEFAULT_TABLE_CAP)]
                    for i, item in enumerate(show_chain):
                        html.append(f"<tr><td>{i+1}</td><td>{self._make_link(item)}</td></tr>")
                    if not self.full and len(chain) > len(show_chain):
                        html.append(
                            f"<tr><td>…</td><td>(+{len(chain) - len(show_chain)} more)</td></tr>"
                        )
                    html.append("</table>")
            else:
                html.append('<div class="summary"><em>No load order detected.</em></div>')

        # Conflicts & Overrides
        if results.get("warnings"):
            html.append("<h3>Conflicts & Overrides</h3>")
            html.append("<table>")
            html.append(
                "<tr><th>Selector</th><th>Property</th><th>Page</th><th>From</th><th>To</th><th>Reason</th></tr>"
            )
            badge_map = {
                "important-blocks-normal": "badge badge-danger",
                "important-vs-important": "badge badge-warning",
                "later-overrides-earlier": "badge badge-info",
                "ambiguous-load-order": "badge badge-warning",
                "dynamic-css": "badge badge-info",
            }
            warns = results["warnings"]
            shown = self._maybe_cap(warns)
            for w in shown:
                reason = w.get("reason", w.get("type", ""))
                cls = badge_map.get(w.get("type", ""), "badge")
                fr = self._format_file_line_html(w.get("from", ""))
                to = self._format_file_line_html(w.get("to", ""))
                html.append(
                    f"<tr><td>{w.get('selector','')}</td><td>{w.get('property','')}</td><td>{w.get('page','')}</td><td>{fr}</td><td>{to}</td><td><span class='{cls}'>{reason}</span></td></tr>"
                )
            html.append("</table>")
            if not self.full and len(warns) > len(shown):
                html.append(
                    f"<p><em>Showing {len(shown)} of {len(warns)} warnings. Use --full to show all.</em></p>"
                )
            html.append(
                '<p><small>Legend: <span class="badge badge-danger">important blocks normal</span> <span class="badge badge-warning">important vs important</span> <span class="badge badge-info">later overrides earlier</span></small></p>'
            )

        # Merged CSS
        if merge and results.get("merged"):
            html.append("<h3>Merged CSS Rules</h3><br>")
            for selector, merged_css in results["merged"].items():
                html.append(f"<pre><code>{merged_css}</code></pre><br>")
        if merge and results.get("merged_per_page"):
            html.append("<h3>Merged CSS Rules (Per Page)</h3>")
            for page, selmap in results["merged_per_page"].items():
                html.append(f"<h4>{page}</h4>")
                for selector, merged_css in selmap.items():
                    html.append(f"<pre><code>{merged_css}</code></pre>")

        return "".join(html)

    def _unused_section(self, results: Dict[str, Any]) -> str:
        """Generate HTML for unused selectors section."""
        html: List[str] = []

        if not results:
            html.append('<div class="error">No data available.</div>')
            return "".join(html)

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
        if results.get("unused_files"):
            html.append("<h3>Unused CSS Files</h3>")
            html.append("<table>")
            html.append("<tr><th>File</th></tr>")
            files = list(results["unused_files"]) or []
            shown = self._maybe_cap(files)
            for f in shown:
                html.append(f"<tr><td>{self._make_link(f)}</td></tr>")
            html.append("</table>")
            if not self.full and len(files) > len(shown):
                html.append(
                    f"<p><em>Showing {len(shown)} of {len(files)} files. Use --full to show all.</em></p>"
                )

        # Unused selectors
        unused = results.get("unused_selectors", {})
        if unused:
            html.append("<h3>Unused Selectors</h3>")
            html.append("<table>")
            html.append("<tr><th>Selector</th><th>File</th><th>Line</th></tr>")

            rows: List[Any] = []
            for selector, locations in unused.items():
                for location in locations:
                    rows.append((selector, location.get("file", ""), location.get("line", "")))
            shown = self._maybe_cap(rows)
            for selector, file_path, line in shown:
                file_cell = (
                    self._format_file_line_html(f"{file_path}:{line}")
                    if self.use_vscode and str(line).isdigit()
                    else self._make_link(file_path)
                )
                html.append(
                    f"<tr><td>{selector}</td><td>{file_cell}</td><td>{line}</td></tr>"
                )
            html.append("</table>")
            if not self.full and len(rows) > len(shown):
                html.append(
                    f"<p><em>Showing {len(shown)} of {len(rows)} occurrences. Use --full to show all.</em></p>"
                )
        else:
            html.append('<div class="success">✓ No unused selectors found.</div>')

        return "".join(html)

    def _structure_section(self, results: Dict[str, Any]) -> str:
        """Generate HTML for structure section."""
        html: List[str] = []

        if not results:
            html.append('<div class="error">No analysis results available.</div>')
            return "".join(html)

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

        # Load order per page
        if "load_order" in results:
            load_order = results.get("load_order") or {}
            non_empty = {pg: ch for pg, ch in load_order.items() if ch}
            html.append("<h3>Load Order (per page)</h3>")
            if non_empty:
                for page, chain in non_empty.items():
                    html.append(f"<h4>{page}</h4>")
                    html.append("<table>")
                    html.append("<tr><th>#</th><th>CSS File</th></tr>")
                    show_chain = chain if self.full else chain[: (self.table_cap or DEFAULT_TABLE_CAP)]
                    for i, item in enumerate(show_chain):
                        html.append(f"<tr><td>{i+1}</td><td>{self._make_link(item)}</td></tr>")
                    if not self.full and len(chain) > len(show_chain):
                        html.append(
                            f"<tr><td>…</td><td>(+{len(chain) - len(show_chain)} more)</td></tr>"
                        )
                    html.append("</table>")
            else:
                html.append('<div class="summary"><em>No load order detected.</em></div>')

        # Prefix analysis
        prefixes = results.get("prefixes", {})
        if prefixes:
            filtered = [(k, v) for k, v in prefixes.items() if v >= 2]
            if filtered:
                html.append("<h3>Prefix Analysis (classes and IDs)</h3>")
                html.append("<table>")
                html.append("<tr><th>Prefix</th><th>Count</th><th>Example Tokens</th></tr>")

                sorted_prefixes = sorted(filtered, key=lambda x: x[1], reverse=True)
                shown = sorted_prefixes if self.full else sorted_prefixes[: (self.table_cap or DEFAULT_TABLE_CAP)]
                for prefix, count in shown:
                    classes = results.get("prefix_groups", {}).get(prefix, [])
                    if self.full:
                        example_classes = ", ".join(classes)
                    else:
                        example_classes = ", ".join(classes[:3])
                        if len(classes) > 3:
                            example_classes += f" (+{len(classes) - 3} more)"
                    html.append(
                        f"<tr><td><code>{prefix}</code></td><td>{count}</td><td>{example_classes}</td></tr>"
                    )

                html.append("</table>")
                if not self.full and len(sorted_prefixes) > len(shown):
                    html.append(
                        f"<p><em>Showing {len(shown)} of {len(sorted_prefixes)} prefixes (count ≥ 2). Use --full to show all.</em></p>"
                    )

        # Comments
        comments = results.get("comments", [])
        if comments:
            html.append(f"<h3>CSS Comments ({len(comments)})</h3>")
            html.append("<table>")
            html.append("<tr><th>File</th><th>Line</th><th>Comment</th></tr>")

            shown = self._maybe_cap(comments)
            for comment in shown:
                text = comment.get("text", "")
                if self.full:
                    comment_text = text
                else:
                    comment_text = text[:80] + "..." if len(text) > 80 else text
                file_cell = (
                    self._format_file_line_html(f"{comment.get('file','')}:{comment.get('line','')}")
                    if self.use_vscode and str(comment.get('line','')).isdigit()
                    else self._make_link(comment.get('file',''))
                )
                html.append(
                    f"<tr><td>{file_cell}</td><td>{comment.get('line','')}</td><td><code>{comment_text}</code></td></tr>"
                )

            html.append("</table>")
            if not self.full and len(comments) > len(shown):
                html.append(
                    f"<p><em>Showing {len(shown)} of {len(comments)} comments. Use --full to show all.</em></p>"
                )

        return "".join(html)
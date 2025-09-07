#!/usr/bin/env python3
"""
Main CLI application for CSS Analyzer.
"""

import click
from rich.console import Console
from pathlib import Path
import sys
import os

# Add the current directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from analyzers import DuplicateAnalyzer, UnusedSelectorAnalyzer, StructureAnalyzer
from reporters import ConsoleReporter, HTMLReporter
from utils import get_css_files, get_source_files, parse_html_for_css, parse_list_option

console = Console()
version="1.4.0"

@click.group()
@click.version_option(version=version, prog_name="main.py")
def cli():
    """A comprehensive CSS analysis tool for web projects.
    
    Analyzes CSS files for duplicates, unused selectors, and structural patterns.
    Supports HTML, PHP, and JS file scanning for unused selector detection.
    """
    # Create reports folder if it doesn't exist
    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)
    

@cli.command()
@click.argument('path', type=click.Path(exists=True, path_type=Path))
@click.option('--output-html', type=click.Path(path_type=Path), 
              help='Generate an HTML report at the specified path.')
@click.option('--merge', is_flag=True, help='Generate merged CSS rules for duplicate selectors.')
@click.option('--per-page-merge', is_flag=True, help='Produce merged CSS per page based on load order.')
@click.option('--page-root', type=click.Path(path_type=Path), help='Root directory where HTML/PHP pages live (defaults to PATH).')
@click.option('--skip', is_flag=True, help='Only include CSS files referenced by pages (requires --page-root or defaults to PATH).')
@click.option('--full', is_flag=True, help='Show all rows in tables (CLI and HTML).')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output.')
@click.option('--vscode', is_flag=True, help='Open links in VS Code (vscode:// deep links).')
@click.option('--blacklist', type=str, default='', help='Comma-separated list of filenames (name.ext) or /dir/ rules to exclude.')
@click.option('--whitelist', type=str, default='', help='Comma-separated list of filenames (name.ext) or /dir/ rules to include exclusively.')
def duplicates(path, output_html, merge, per_page_merge, page_root, skip, full, verbose, vscode, blacklist, whitelist):
    """Find duplicate selectors, @media rules, and comments."""
    if verbose:
        console.print(f"[yellow]Analyzing duplicates in: {path}[/yellow]")
    
    # Get CSS files to analyze
    wl = parse_list_option(whitelist)
    bl = parse_list_option(blacklist)
    # Build page mapping for load order (always)
    root = page_root or path
    if verbose:
        console.print(f"[yellow]Building page load order from: {root}[/yellow]")
    page_info = parse_html_for_css(root, whitelist=wl, blacklist=bl)

    # Get CSS files to analyze (after parsing page map)
    css_files = get_css_files(path, whitelist=wl, blacklist=bl)
    if not css_files:
        console.print("[yellow]No CSS files found in the specified path. Showing load order only (if any).[/yellow]")
    else:
        if verbose:
            console.print(f"[green]Found {len(css_files)} CSS files to analyze[/green]")
    
    # page_info already built above; keep it regardless of flags so load order is shown

    # Perform analysis
    analyzer = DuplicateAnalyzer()
    results = analyzer.analyze(css_files, merge=merge, page_map=page_info, per_page_merge=per_page_merge, skip_unreferenced=skip)
    
    # Report results
    console_reporter = ConsoleReporter(project_root=Path(path).resolve(), full=full, use_vscode=vscode)
    console_reporter.report_duplicates(results, merge=merge)
    
    if output_html:
        html_reporter = HTMLReporter(project_root=Path(path).resolve(), full=full, use_vscode=vscode)
        html_reporter.generate_report(results, output_html, analysis_type='duplicates', merge=merge)
        console.print(f"[green]HTML report generated: {output_html}[/green]")

@cli.command()
@click.argument('path', type=click.Path(exists=True, path_type=Path))
@click.option('--output-html', type=click.Path(path_type=Path), 
              help='Generate an HTML report at the specified path.')
@click.option('--page-root', type=click.Path(path_type=Path), help='Root directory where HTML/PHP pages live (defaults to PATH).')
@click.option('--skip', is_flag=True, help='Only include CSS files referenced by pages (requires --page-root or defaults to PATH).')
@click.option('--full', is_flag=True, help='Show all rows in tables (CLI and HTML).')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output.')
@click.option('--vscode', is_flag=True, help='Open links in VS Code (vscode:// deep links).')
@click.option('--blacklist', type=str, default='', help='Comma-separated list of filenames (name.ext) or /dir/ rules to exclude.')
@click.option('--whitelist', type=str, default='', help='Comma-separated list of filenames (name.ext) or /dir/ rules to include exclusively.')
def unused(path, output_html, page_root, skip, full, verbose, vscode, blacklist, whitelist):
    """Find unused CSS selectors by scanning HTML, PHP, and JS files."""
    if verbose:
        console.print(f"[yellow]Analyzing unused selectors in: {path}[/yellow]")
    
    # Get CSS and source files
    wl = parse_list_option(whitelist)
    bl = parse_list_option(blacklist)
    css_files = get_css_files(path, whitelist=wl, blacklist=bl)
    source_files = get_source_files(path, whitelist=wl, blacklist=bl)
    
    if not css_files:
        console.print("[red]No CSS files found in the specified path.[/red]")
        return
    
    if not source_files:
        console.print("[yellow]No source files (HTML, PHP, JS) found. Selector usage analysis may be limited.[/yellow]")
    
    if verbose:
        console.print(f"[green]Found {len(css_files)} CSS files and {len(source_files)} source files[/green]")
    
    # Page mapping
    page_info = parse_html_for_css(page_root or path, whitelist=wl, blacklist=bl)

    # Perform analysis
    analyzer = UnusedSelectorAnalyzer()
    results = analyzer.analyze(css_files, source_files, page_map=page_info, skip_unreferenced=skip)
    
    # Report results
    console_reporter = ConsoleReporter(project_root=Path(path).resolve(), full=full, use_vscode=vscode)
    console_reporter.report_unused_selectors(results)
    
    if output_html:
        html_reporter = HTMLReporter(project_root=Path(path).resolve(), full=full, use_vscode=vscode)
        html_reporter.generate_report(results, output_html, analysis_type='unused')
        console.print(f"[green]HTML report generated: {output_html}[/green]")

@cli.command()
@click.argument('path', type=click.Path(exists=True, path_type=Path))
@click.option('--output-html', type=click.Path(path_type=Path), 
              help='Generate an HTML report at the specified path.')
@click.option('--page-root', type=click.Path(path_type=Path), help='Root directory where HTML/PHP pages live (defaults to PATH).')
@click.option('--skip', is_flag=True, help='Only include CSS files referenced by pages (requires --page-root or defaults to PATH).')
@click.option('--full', is_flag=True, help='Show all rows in tables (CLI and HTML).')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output.')
@click.option('--vscode', is_flag=True, help='Open links in VS Code (vscode:// deep links).')
@click.option('--blacklist', type=str, default='', help='Comma-separated list of filenames (name.ext) or /dir/ rules to exclude.')
@click.option('--whitelist', type=str, default='', help='Comma-separated list of filenames (name.ext) or /dir/ rules to include exclusively.')
def structure(path, output_html, page_root, skip, full, verbose, vscode, blacklist, whitelist):
    """Analyze CSS structure for prefixes, comments, and patterns."""
    if verbose:
        console.print(f"[yellow]Analyzing CSS structure in: {path}[/yellow]")
    
    # Build CSS filters and page map
    wl = parse_list_option(whitelist)
    bl = parse_list_option(blacklist)
    root = page_root or path
    if verbose:
        console.print(f"[yellow]Building page load order from: {root}[/yellow]")
    page_info = parse_html_for_css(root, whitelist=wl, blacklist=bl)

    # Get CSS files to analyze
    css_files = get_css_files(path, whitelist=wl, blacklist=bl)
    if not css_files:
        console.print("[yellow]No CSS files found in the specified path. Showing load order only (if any).[/yellow]")
    else:
        if verbose:
            console.print(f"[green]Found {len(css_files)} CSS files to analyze[/green]")

    # Perform analysis
    analyzer = StructureAnalyzer()
    results = analyzer.analyze(css_files, page_map=page_info, skip_unreferenced=skip)
    
    # Report results
    console_reporter = ConsoleReporter(project_root=Path(path).resolve(), full=full, use_vscode=vscode)
    console_reporter.report_structure(results)
    
    if output_html:
        html_reporter = HTMLReporter(project_root=Path(path).resolve(), full=full, use_vscode=vscode)
        html_reporter.generate_report(results, output_html, analysis_type='structure')
        console.print(f"[green]HTML report generated: {output_html}[/green]")

@cli.command()
@click.argument('path', type=click.Path(exists=True, path_type=Path))
@click.option('--output-html', type=click.Path(path_type=Path), 
              help='Generate an HTML report at the specified path.')
@click.option('--page-root', type=click.Path(path_type=Path), help='Root directory where HTML/PHP pages live (defaults to PATH).')
@click.option('--full', is_flag=True, help='Show all rows in tables (CLI and HTML).')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output.')
@click.option('--vscode', is_flag=True, help='Open links in VS Code (vscode:// deep links).')
@click.option('--blacklist', type=str, default='', help='Comma-separated list of filenames (name.ext) or /dir/ rules to exclude.')
@click.option('--whitelist', type=str, default='', help='Comma-separated list of filenames (name.ext) or /dir/ rules to include exclusively.')
def analyze(path, output_html, page_root, full, verbose, vscode, blacklist, whitelist):
    """Run all analyses (duplicates, unused, structure)."""
    if verbose:
        console.print(f"[yellow]Running comprehensive analysis on: {path}[/yellow]")
    
    # Get all files
    wl = parse_list_option(whitelist)
    bl = parse_list_option(blacklist)
    css_files = get_css_files(path, whitelist=wl, blacklist=bl)
    source_files = get_source_files(path, whitelist=wl, blacklist=bl)
    
    if not css_files:
        console.print("[red]No CSS files found in the specified path.[/red]")
        return
    
    if verbose:
        console.print(f"[green]Found {len(css_files)} CSS files and {len(source_files)} source files[/green]")
    
    # Build page mapping once
    page_info = parse_html_for_css(page_root or path, whitelist=wl, blacklist=bl)

    # Perform all analyses
    all_results = {}
    
    # Duplicates analysis
    console.print("[cyan]Analyzing duplicates...[/cyan]")
    duplicate_analyzer = DuplicateAnalyzer()
    all_results['duplicates'] = duplicate_analyzer.analyze(css_files, merge=False, page_map=page_info)
    
    # Unused selectors analysis
    console.print("[cyan]Analyzing unused selectors...[/cyan]")
    unused_analyzer = UnusedSelectorAnalyzer()
    all_results['unused'] = unused_analyzer.analyze(css_files, source_files, page_map=page_info)
    
    # Structure analysis
    console.print("[cyan]Analyzing structure...[/cyan]")
    structure_analyzer = StructureAnalyzer()
    all_results['structure'] = structure_analyzer.analyze(css_files, page_map=page_info)
    
    # Report results
    console_reporter = ConsoleReporter(project_root=Path(path).resolve(), full=full, use_vscode=vscode)
    console_reporter.report_comprehensive(all_results)
    
    if output_html:
        html_reporter = HTMLReporter(project_root=Path(path).resolve(), full=full, use_vscode=vscode)
        html_reporter.generate_comprehensive_report(all_results, output_html)
        console.print(f"[green]Comprehensive HTML report generated: {output_html}[/green]")

if __name__ == '__main__':
    cli()
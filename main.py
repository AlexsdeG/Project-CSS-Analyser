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
from utils import get_css_files, get_source_files

console = Console()

@click.group()
@click.version_option()
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
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output.')
def duplicates(path, output_html, merge, verbose):
    """Find duplicate selectors, @media rules, and comments."""
    if verbose:
        console.print(f"[yellow]Analyzing duplicates in: {path}[/yellow]")
    
    # Get CSS files to analyze
    css_files = get_css_files(path)
    if not css_files:
        console.print("[red]No CSS files found in the specified path.[/red]")
        return
    
    if verbose:
        console.print(f"[green]Found {len(css_files)} CSS files to analyze[/green]")
    
    # Perform analysis
    analyzer = DuplicateAnalyzer()
    results = analyzer.analyze(css_files, merge=merge)
    
    # Report results
    console_reporter = ConsoleReporter()
    console_reporter.report_duplicates(results, merge=merge)
    
    if output_html:
        html_reporter = HTMLReporter()
        html_reporter.generate_report(results, output_html, analysis_type='duplicates', merge=merge)
        console.print(f"[green]HTML report generated: {output_html}[/green]")

@cli.command()
@click.argument('path', type=click.Path(exists=True, path_type=Path))
@click.option('--output-html', type=click.Path(path_type=Path), 
              help='Generate an HTML report at the specified path.')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output.')
def unused(path, output_html, verbose):
    """Find unused CSS selectors by scanning HTML, PHP, and JS files."""
    if verbose:
        console.print(f"[yellow]Analyzing unused selectors in: {path}[/yellow]")
    
    # Get CSS and source files
    css_files = get_css_files(path)
    source_files = get_source_files(path)
    
    if not css_files:
        console.print("[red]No CSS files found in the specified path.[/red]")
        return
    
    if not source_files:
        console.print("[yellow]No source files (HTML, PHP, JS) found. Selector usage analysis may be limited.[/yellow]")
    
    if verbose:
        console.print(f"[green]Found {len(css_files)} CSS files and {len(source_files)} source files[/green]")
    
    # Perform analysis
    analyzer = UnusedSelectorAnalyzer()
    results = analyzer.analyze(css_files, source_files)
    
    # Report results
    console_reporter = ConsoleReporter()
    console_reporter.report_unused_selectors(results)
    
    if output_html:
        html_reporter = HTMLReporter()
        html_reporter.generate_report(results, output_html, analysis_type='unused')
        console.print(f"[green]HTML report generated: {output_html}[/green]")

@cli.command()
@click.argument('path', type=click.Path(exists=True, path_type=Path))
@click.option('--output-html', type=click.Path(path_type=Path), 
              help='Generate an HTML report at the specified path.')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output.')
def structure(path, output_html, verbose):
    """Analyze CSS structure for prefixes, comments, and patterns."""
    if verbose:
        console.print(f"[yellow]Analyzing CSS structure in: {path}[/yellow]")
    
    # Get CSS files to analyze
    css_files = get_css_files(path)
    if not css_files:
        console.print("[red]No CSS files found in the specified path.[/red]")
        return
    
    if verbose:
        console.print(f"[green]Found {len(css_files)} CSS files to analyze[/green]")
    
    # Perform analysis
    analyzer = StructureAnalyzer()
    results = analyzer.analyze(css_files)
    
    # Report results
    console_reporter = ConsoleReporter()
    console_reporter.report_structure(results)
    
    if output_html:
        html_reporter = HTMLReporter()
        html_reporter.generate_report(results, output_html, analysis_type='structure')
        console.print(f"[green]HTML report generated: {output_html}[/green]")

@cli.command()
@click.argument('path', type=click.Path(exists=True, path_type=Path))
@click.option('--output-html', type=click.Path(path_type=Path), 
              help='Generate an HTML report at the specified path.')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output.')
def analyze(path, output_html, verbose):
    """Run all analyses (duplicates, unused, structure)."""
    if verbose:
        console.print(f"[yellow]Running comprehensive analysis on: {path}[/yellow]")
    
    # Get all files
    css_files = get_css_files(path)
    source_files = get_source_files(path)
    
    if not css_files:
        console.print("[red]No CSS files found in the specified path.[/red]")
        return
    
    if verbose:
        console.print(f"[green]Found {len(css_files)} CSS files and {len(source_files)} source files[/green]")
    
    # Perform all analyses
    all_results = {}
    
    # Duplicates analysis
    console.print("[cyan]Analyzing duplicates...[/cyan]")
    duplicate_analyzer = DuplicateAnalyzer()
    all_results['duplicates'] = duplicate_analyzer.analyze(css_files)
    
    # Unused selectors analysis
    console.print("[cyan]Analyzing unused selectors...[/cyan]")
    unused_analyzer = UnusedSelectorAnalyzer()
    all_results['unused'] = unused_analyzer.analyze(css_files, source_files)
    
    # Structure analysis
    console.print("[cyan]Analyzing structure...[/cyan]")
    structure_analyzer = StructureAnalyzer()
    all_results['structure'] = structure_analyzer.analyze(css_files)
    
    # Report results
    console_reporter = ConsoleReporter()
    console_reporter.report_comprehensive(all_results)
    
    if output_html:
        html_reporter = HTMLReporter()
        html_reporter.generate_comprehensive_report(all_results, output_html)
        console.print(f"[green]Comprehensive HTML report generated: {output_html}[/green]")

if __name__ == '__main__':
    cli()
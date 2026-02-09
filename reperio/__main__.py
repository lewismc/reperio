# type: ignore[attr-defined]
"""Reperio CLI application."""

import os
import webbrowser
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from reperio import version
from reperio.config import get_config
from reperio.graph.graph_builder import GraphBuilder
from reperio.parsers.crawldb_parser import CrawlDBParser
from reperio.parsers.linkdb_parser import LinkDBParser
from reperio.readers.database_reader import create_nutch_reader, discover_nutch_partitions
from reperio.readers.filesystem import FileSystemManager

app = typer.Typer(
    name="reperio",
    help="Reperio - Visualization utility for Apache Nutch data structures.",
    add_completion=False,
)
console = Console()


def version_callback(print_version: bool) -> None:
    """Print the version of the package."""
    if print_version:
        console.print(f"[yellow]reperio[/] version: [bold blue]{version}[/]")
        raise typer.Exit()


@app.callback()
def main(
    print_version: bool = typer.Option(
        False,
        "--version",
        callback=version_callback,
        is_eager=True,
        help="Print version and exit.",
    ),
) -> None:
    """Reperio - Visualization utility for Apache Nutch data structures.
    
    For statistics, use Nutch's built-in tools:
        nutch readdb /path/to/crawldb -stats
        nutch readlinkdb /path/to/linkdb -stats
        nutch readhostdb /path/to/hostdb -stats
    
    Reperio focuses on visualization and graph analysis."""
    pass


@app.command()
def serve(
    crawldb: Optional[str] = typer.Option(None, "--crawldb", help="Path to CrawlDB"),
    linkdb: Optional[str] = typer.Option(None, "--linkdb", help="Path to LinkDB"),
    hostdb: Optional[str] = typer.Option(None, "--hostdb", help="Path to HostDB"),
    host: str = typer.Option("0.0.0.0", "--host", help="API server host"),
    port: int = typer.Option(8000, "--port", help="API server port"),
    max_records: Optional[int] = typer.Option(None, "--max-records", help="Maximum records to load per dataset"),
    reload: bool = typer.Option(False, "--reload", help="Enable auto-reload"),
    namenode: Optional[str] = typer.Option(None, "--namenode", help="HDFS namenode hostname"),
    hdfs_port: Optional[int] = typer.Option(None, "--hdfs-port", help="HDFS namenode port"),
):
    """Start API server with Nutch SequenceFile data loaded.
    
    Load one or more Nutch datasets (CrawlDB, LinkDB, HostDB) and serve via REST API.
    All specified datasets will be loaded and available for visualization.
    
    Examples:
        # Load single dataset
        reperio serve --crawldb /path/to/crawldb
        
        # Load multiple datasets
        reperio serve --crawldb /path/to/crawldb --linkdb /path/to/linkdb
        
        # Load all three
        reperio serve --crawldb /path/to/crawldb --linkdb /path/to/linkdb --hostdb /path/to/hostdb
        
        # From HDFS
        reperio serve --crawldb hdfs://namenode:9000/nutch/crawldb --linkdb hdfs://namenode:9000/nutch/linkdb
    """
    # Validate that at least one dataset is specified
    datasets_to_load = []
    if crawldb:
        datasets_to_load.append(("crawldb", crawldb))
    if linkdb:
        datasets_to_load.append(("linkdb", linkdb))
    if hostdb:
        datasets_to_load.append(("hostdb", hostdb))
    
    if not datasets_to_load:
        console.print("[red]Error:[/] At least one dataset must be specified (--crawldb, --linkdb, or --hostdb)")
        raise typer.Exit(1)
    
    console.print(f"[bold blue]Starting Reperio API server on {host}:{port}[/]")
    console.print(f"[cyan]Loading {len(datasets_to_load)} dataset(s)...[/]")
    
    try:
        config = get_config()
        import uvicorn
        from reperio.api.main import app as fastapi_app, add_dataset
        
        # Define progress callback for multi-partition reading
        def progress_callback(partition_num, total_partitions, partition_path):
            partition_name = os.path.basename(os.path.dirname(partition_path))
            console.print(f"  [cyan]Reading partition {partition_num}/{total_partitions}: {partition_name}[/]")
        
        # Load each dataset
        loaded_count = 0
        for db_type, data_path in datasets_to_load:
            console.print(f"\n[bold cyan]Loading {db_type.upper()}:[/] {data_path}")
            
            try:
                # Create filesystem manager
                fs_manager = FileSystemManager.create(
                    path=data_path,
                    namenode=namenode or config.hdfs_namenode,
                    port=hdfs_port or config.hdfs_port,
                )
                
                # Discover partition files
                try:
                    partition_files = discover_nutch_partitions(data_path, fs_manager)
                    if len(partition_files) > 1:
                        console.print(f"  [cyan]Found {len(partition_files)} partition file(s)[/]")
                    else:
                        console.print(f"  [cyan]Reading single partition[/]")
                except (FileNotFoundError, ValueError) as e:
                    console.print(f"  [red]Error:[/] {e}")
                    fs_manager.close()
                    continue  # Skip this dataset but continue with others
                
                # Create appropriate reader
                reader = create_nutch_reader(
                    path=data_path,
                    db_type=db_type,
                    fs_manager=fs_manager,
                    progress_callback=progress_callback,
                )
                
                # Build graph
                console.print(f"  [cyan]Building {db_type} graph...[/]")
                builder = GraphBuilder()
                
                if db_type.lower() == "crawldb":
                    parser = CrawlDBParser(reader)
                    builder.from_crawldb(parser, max_records=max_records)
                    graph = builder.get_graph()
                    loaded_count += 1
                elif db_type.lower() == "linkdb":
                    parser = LinkDBParser(reader)
                    builder.from_linkdb(parser, max_records=max_records)
                    graph = builder.get_graph()
                    loaded_count += 1
                elif db_type.lower() == "hostdb":
                    console.print(f"  [yellow]Note:[/] HostDB is for statistics only, not graph visualization")
                    fs_manager.close()
                    continue
                else:
                    console.print(f"  [red]Error:[/] Unsupported type: {db_type}")
                    fs_manager.close()
                    continue
                
                console.print(f"  [green]✓[/] {db_type.upper()} loaded: {graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges")
                
                # Store dataset in API
                metadata = {
                    "db_type": db_type,
                    "path": data_path,
                    "num_nodes": graph.number_of_nodes(),
                    "num_edges": graph.number_of_edges(),
                }
                add_dataset(db_type, graph, builder, metadata)
                
                fs_manager.close()
                
            except Exception as e:
                console.print(f"  [red]Error loading {db_type}:[/] {e}")
                continue  # Continue loading other datasets
        
        # Check if any datasets were successfully loaded
        if loaded_count == 0:
            console.print(f"\n[red]Error:[/] No datasets were successfully loaded")
            raise typer.Exit(1)
        
        console.print(f"\n[cyan]API docs:[/] http://{host}:{port}/docs")
        console.print(f"[cyan]Visualization:[/] http://{host}:{port}/")
        console.print(f"[green]✓[/] Server ready with {loaded_count} dataset(s)!")
        
        uvicorn.run(fastapi_app, host=host, port=port, reload=reload)
        
    except ImportError as e:
        if "fastapi" in str(e) or "uvicorn" in str(e):
            console.print("[red]Error:[/] FastAPI and uvicorn required. Install with: pip install fastapi uvicorn")
        else:
            console.print(f"[red]Error:[/] {str(e)}")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Fatal error:[/] {str(e)}")
        raise typer.Exit(1)


@app.command()
def web(
    crawldb: Optional[str] = typer.Option(None, "--crawldb", help="Path to CrawlDB"),
    linkdb: Optional[str] = typer.Option(None, "--linkdb", help="Path to LinkDB"),
    hostdb: Optional[str] = typer.Option(None, "--hostdb", help="Path to HostDB"),
    port: int = typer.Option(8000, "--port", help="API server port"),
    max_records: Optional[int] = typer.Option(None, "--max-records", help="Maximum records to load per dataset"),
    open_browser: bool = typer.Option(True, "--open/--no-open", help="Open browser automatically"),
    namenode: Optional[str] = typer.Option(None, "--namenode", help="HDFS namenode hostname"),
    hdfs_port: Optional[int] = typer.Option(None, "--hdfs-port", help="HDFS namenode port"),
):
    """Launch web UI with your Nutch SequenceFile data (one command!).
    
    The easiest way to visualize Nutch data. Load one or more datasets and explore them
    interactively in the browser. Switch between loaded datasets in the frontend.
    
    Examples:
        # Load single dataset
        reperio web --crawldb /path/to/crawldb
        
        # Load multiple datasets (recommended!)
        reperio web --crawldb /path/to/crawldb --linkdb /path/to/linkdb
        
        # Load all three datasets
        reperio web --crawldb /path/to/crawldb --linkdb /path/to/linkdb --hostdb /path/to/hostdb
        
        # From HDFS
        reperio web --crawldb hdfs://namenode:9000/nutch/crawldb --linkdb hdfs://namenode:9000/nutch/linkdb
    
    For statistics, use Nutch tools:
        nutch readdb /path/to/crawldb -stats
        nutch readlinkdb /path/to/linkdb -stats
    """
    console.print("[bold blue]Launching Reperio web interface...[/]")
    
    # Check if frontend is built
    frontend_dir = Path(__file__).parent.parent / "frontend" / "dist"
    frontend_built = frontend_dir.exists() and (frontend_dir / "index.html").exists()
    
    if not frontend_built:
        console.print("[yellow]⚠ Frontend not built - interactive visualization unavailable[/]")
        console.print("[cyan]To enable visualization:[/] cd frontend && npm run build")
        console.print("[cyan]API endpoints:[/] http://localhost:{port}/docs")
    else:
        console.print("[green]✓[/] Frontend ready for interactive visualization")
    
    # Open browser before starting server (so user sees it starting)
    if open_browser:
        url = f"http://localhost:{port}"
        console.print(f"[cyan]Opening browser:[/] {url}")
        webbrowser.open(url)
    
    # Start server with data loaded
    serve(
        crawldb=crawldb,
        linkdb=linkdb,
        hostdb=hostdb,
        host="localhost",
        port=port,
        max_records=max_records,
        reload=False,
        namenode=namenode,
        hdfs_port=hdfs_port,
    )


if __name__ == "__main__":
    app()

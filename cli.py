import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.orchestrator import NeuroOrchestrator
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

def main():
    console.print(Panel.fit("[bold green]NeuroOps Autonomous System[/bold green]", border_style="green"))
    
    goal = console.input("\n[bold yellow]Enter your high-level goal:[/bold yellow] ")
    
    if not goal.strip():
        console.print("[red]Goal cannot be empty.[/red]")
        return

    orchestrator = NeuroOrchestrator()
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
        console=console
    ) as progress:
        progress.add_task(description="Initializing...", total=None)
        
        # Run Logic
        result = orchestrator.run(goal)
    
    # Display Results
    console.print("\n[bold blue]=== PLAN ===[/bold blue]")
    for i, task in enumerate(result['plan'], 1):
        console.print(f"{i}. {task}")
    
    console.print("\n[bold cyan]=== EXECUTION LOG ===[/bold cyan]")
    for item in result['execution']:
        console.print(f"🔹 Task: {item['task']}")
        console.print(f"   🛠 Tool: {item['tool_used']}")
        console.print(f"   ✅ Result: {item['result'][:100]}..." if len(str(item['result'])) > 100 else f"   ✅ Result: {item['result']}")
        console.print("")

    console.print(Panel(Markdown(result['final_output']), title="[bold magenta]FINAL OUTPUT[/bold magenta]", border_style="magenta"))
    console.print(f"\n⏱ Completed in {result['duration_seconds']} seconds.")

if __name__ == "__main__":
    main()
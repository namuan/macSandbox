#!/usr/bin/env -S uv run --quiet --script
# /// script
# dependencies = [
#   "rich",
# ]
# ///
"""
sandbox - Run AI agents in isolated Docker containers

Usage:
./sandbox.py -h
./sandbox.py --agent claude
./sandbox.py --agent claude "refactor this codebase"

./sandbox.py -v   # INFO logging
./sandbox.py -vv  # DEBUG logging
"""

import logging
import os
import shutil
import subprocess
import sys
from argparse import ArgumentParser, RawDescriptionHelpFormatter
from pathlib import Path

from rich.console import Console

console = Console()

DEFAULT_MEMORY = "4G"
DEFAULT_CPUS = "2"
INSTANCE_PREFIX = "sandbox"


def setup_logging(verbosity):
    logging_level = logging.WARNING
    if verbosity == 1:
        logging_level = logging.INFO
    elif verbosity >= 2:
        logging_level = logging.DEBUG

    logging.basicConfig(
        handlers=[logging.StreamHandler()],
        format="%(asctime)s - %(filename)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        level=logging_level,
    )
    logging.captureWarnings(capture=True)


def resolve_agent(agent_name: str) -> dict:
    return {
        "name": agent_name,
        "image": f"sandbox-{agent_name}:latest",
        "dockerfile": f"Dockerfile.{agent_name}",
    }


def build_image(agent_config: dict):
    dockerfile = agent_config["dockerfile"]
    df_path = Path(__file__).resolve().parent / dockerfile
    if not df_path.exists():
        console.print(f"[red]Error: Dockerfile not found: {df_path}[/red]")
        sys.exit(1)

    image = agent_config["image"]
    console.print(f"[blue]Building image '{image}' from {dockerfile}...[/blue]")
    result = subprocess.run(
        ["docker", "build", "-t", image, "-f", str(df_path), str(df_path.parent)]
    )
    if result.returncode == 0:
        console.print(f"[green]Successfully built '{image}'[/green]")
    else:
        console.print("[red]Build failed[/red]")
        sys.exit(result.returncode)


def check_prerequisites(agent_config: dict):
    if not shutil.which("docker"):
        console.print("[red]Error: Docker not found[/red]")
        console.print("Install Docker Desktop from: https://www.docker.com/products/docker-desktop/")
        sys.exit(1)

    if subprocess.run(["docker", "info"], capture_output=True).returncode != 0:
        console.print("[red]Error: Docker daemon is not running[/red]")
        console.print("Start Docker Desktop and try again.")
        sys.exit(1)

    image = agent_config["image"]
    if subprocess.run(["docker", "image", "inspect", image], capture_output=True).returncode != 0:
        console.print(f"[red]Error: Image '{image}' not found[/red]")
        console.print(f"Build it with: ./sandbox.py --agent {agent_config['name']} --build")
        sys.exit(1)


def run_instance(agent_config: dict, workspace_dir: Path, memory: str, cpus: str, agent_args: list[str]):
    instance_name = f"{INSTANCE_PREFIX}-{agent_config['name']}-{workspace_dir.name}-{os.getpid()}"

    run_cmd = [
        "docker", "run",
        "--name", instance_name,
        "--rm", "-it",
        f"--memory={memory}",
        f"--cpus={cpus}",
        "-v", f"{workspace_dir}:/workspace",
        "-w", "/workspace",
        agent_config["image"],
        *agent_args,
    ]

    logging.debug(f"Running: {' '.join(run_cmd)}")
    subprocess.run(run_cmd)


def parse_args():
    parser = ArgumentParser(description=__doc__, formatter_class=RawDescriptionHelpFormatter)
    parser.add_argument(
        "-v", "--verbose",
        action="count",
        default=0,
        help="Increase verbosity of logging output",
    )
    parser.add_argument(
        "--agent",
        default="claude",
        metavar="NAME",
        help="Agent to run (default: claude)",
    )
    parser.add_argument(
        "--memory",
        default=None,
        help="Memory limit, e.g. 4G (default: SANDBOX_MEMORY env or 4G)",
    )
    parser.add_argument(
        "--cpus",
        default=None,
        help="CPU cores (default: SANDBOX_CPUS env or 2)",
    )
    parser.add_argument(
        "--build",
        action="store_true",
        help="Build the Docker image for the selected agent and exit",
    )
    parser.add_argument(
        "agent_args",
        nargs="*",
        help="Arguments passed through to the agent",
    )
    return parser.parse_args()


def main(args):
    agent_config = resolve_agent(args.agent)
    logging.debug(f"Agent config: {agent_config}")

    if args.build:
        build_image(agent_config)
        return

    check_prerequisites(agent_config)

    workspace_dir = Path.cwd()
    memory = args.memory or os.environ.get("SANDBOX_MEMORY", DEFAULT_MEMORY)
    cpus = args.cpus or os.environ.get("SANDBOX_CPUS", DEFAULT_CPUS)

    run_instance(agent_config, workspace_dir, memory, cpus, args.agent_args)


if __name__ == "__main__":
    args = parse_args()
    setup_logging(args.verbose)
    main(args)

"""
Local CLI interface for the Meta-Orchestrator.

Usage:
  python interfaces/cli.py "set up the SDR fleet for fintech companies 50-200 employees"
  python interfaces/cli.py --interactive
"""

from __future__ import annotations

import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(override=True)

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from orchestrator.agent import MetaOrchestrator


def run_single(message: str) -> None:
    orchestrator = MetaOrchestrator()
    print(f"\n[You] {message}\n")
    response = orchestrator.chat(message)
    print(f"[Orchestrator] {response}\n")


def run_interactive() -> None:
    orchestrator = MetaOrchestrator()
    history: list[dict[str, str]] = []

    print("=== Agent Company CLI ===")
    print("Type your message. Ctrl+C or 'exit' to quit.\n")

    while True:
        try:
            user_input = input("[You] ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye.")
            break

        if user_input.lower() in ("exit", "quit", "q"):
            break
        if not user_input:
            continue

        history.append({"role": "user", "content": user_input})

        try:
            response = orchestrator.chat(user_input, history=history[:-1])
        except Exception as exc:
            response = f"Error: {exc}"

        history.append({"role": "assistant", "content": response})
        print(f"\n[Orchestrator] {response}\n")


if __name__ == "__main__":
    args = sys.argv[1:]

    if not args or "--interactive" in args or "-i" in args:
        run_interactive()
    else:
        run_single(" ".join(args))

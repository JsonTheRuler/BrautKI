from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NPM_BIN = "npm.cmd" if sys.platform.startswith("win") else "npm"


def run_step(command: list[str], cwd: Path) -> None:
    print(f"\n[release-smoke] Running in {cwd}: {' '.join(command)}")
    subprocess.run(command, cwd=str(cwd), check=True)


def main() -> None:
    # Gateway checks
    run_step([NPM_BIN, "install"], ROOT / "gateway")
    run_step([NPM_BIN, "run", "build"], ROOT / "gateway")

    # Agents checks
    run_step([sys.executable, "-m", "pip", "install", "-e", "."], ROOT / "agents")
    run_step([sys.executable, "-m", "compileall", "src"], ROOT / "agents")
    run_step([sys.executable, "-m", "agents.scripts.test_core_agents"], ROOT / "agents")

    # Data checks
    run_step([sys.executable, "-m", "pip", "install", "-e", "."], ROOT / "data")
    run_step([sys.executable, "-m", "compileall", "src", "alembic"], ROOT / "data")
    run_step([sys.executable, "-m", "alembic", "-c", "alembic.ini", "history"], ROOT / "data")

    # Council checks
    run_step([sys.executable, "-m", "pip", "install", "-e", "."], ROOT / "governance" / "llm-council")
    run_step([sys.executable, "-m", "compileall", "src"], ROOT / "governance" / "llm-council")

    print("\n[release-smoke] All release control checks passed.")


if __name__ == "__main__":
    main()

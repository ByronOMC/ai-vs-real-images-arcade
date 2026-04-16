"""
Notas iniciales para Eduardo.
No ejecuta nada todavía; sirve como punto de partida.
"""

from dataclasses import dataclass


@dataclass
class ExecutionPlan:
    frequency: str
    rationale: str
    recommended_runner: str
    ssh_needed: bool


OPTIONS = [
    ExecutionPlan(
        frequency="Monthly",
        rationale="La galería 'Pictures of the month' cambia una vez por mes. Suficiente para este caso.",
        recommended_runner="Cron / GitHub Actions / server interno",
        ssh_needed=False,
    ),
    ExecutionPlan(
        frequency="Daily",
        rationale="Útil solo si luego cambian a otras galerías de Reuters o múltiples fuentes.",
        recommended_runner="Cron job o scheduler central",
        ssh_needed=True,
    ),
]


def main() -> None:
    print("Suggested execution plans:\n")
    for option in OPTIONS:
        print(f"- Frequency: {option.frequency}")
        print(f"  Why: {option.rationale}")
        print(f"  Runner: {option.recommended_runner}")
        print(f"  SSH needed: {option.ssh_needed}\n")


if __name__ == "__main__":
    main()

"""🛑 Runaway agent demo — watch Magicrails save your wallet.

A "customer support agent" gets stuck in a reasoning loop, repeatedly
calling expensive tools. Without a guard it would burn money until you
noticed. Magicrails halts it in milliseconds.

Run:
    python examples/runaway_agent.py

Record a clip for sharing (asciinema → GIF):
    asciinema rec -c "python examples/runaway_agent.py" save.cast
    agg save.cast save.gif --speed 1.0 --theme monokai
"""
from __future__ import annotations

import sys
import time

from magicrails import Magicrails, TripError

# ──────────────────────────────────────────────────────────────────────
# config
BUDGET_USD = 5.00
MODEL = "claude-opus-4-7"           # $5 / $25 per 1M tokens
TOKENS_IN_PER_STEP = 20_000          # context grows each iteration
TOKENS_OUT_PER_STEP = 5_000          # the agent rambles
STEP_DELAY_S = 0.15                  # pacing for the demo
ROTATION = [
    "thinking…",
    "calling search_orders(customer=1124)",
    "thinking…",
    "calling check_refund_eligibility(order=null)",
    "thinking…",
    "calling search_orders(customer=1124)",
]

# ──────────────────────────────────────────────────────────────────────
# tiny ANSI helpers (no deps)
def _supports_color() -> bool:
    return sys.stdout.isatty()


_C = _supports_color()
RESET = "\033[0m" if _C else ""
BOLD = "\033[1m" if _C else ""
DIM = "\033[2m" if _C else ""
RED = "\033[91m" if _C else ""
YELLOW = "\033[93m" if _C else ""
GREEN = "\033[92m" if _C else ""
CYAN = "\033[96m" if _C else ""
GRAY = "\033[90m" if _C else ""


def _bar(spent: float, budget: float, width: int = 24) -> str:
    pct = min(spent / budget, 1.0)
    filled = int(width * pct)
    return "█" * filled + "░" * (width - filled)


def _bar_color(spent: float, budget: float) -> str:
    pct = spent / budget
    if pct < 0.5:
        return GREEN
    if pct < 0.85:
        return YELLOW
    return RED


def _banner() -> None:
    rule = f"{CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}"
    print()
    print(rule)
    print(f"  {BOLD}🤖 Customer Support Agent — Task #4729{RESET}")
    print(f"  {DIM}task   :{RESET} refund a duplicate charge for customer #1124")
    print(f"  {DIM}model  :{RESET} {MODEL}")
    print(f"  {DIM}budget :{RESET} ${BUDGET_USD:.2f}   {DIM}(Magicrails 🛑 watching){RESET}")
    print(rule)
    print()


def main() -> None:
    _banner()
    time.sleep(0.7)

    step = 0
    with Magicrails(budget_usd=BUDGET_USD) as session:
        try:
            while True:
                step += 1
                action = ROTATION[(step - 1) % len(ROTATION)]
                session.record_tokens(
                    model=MODEL,
                    input=TOKENS_IN_PER_STEP,
                    output=TOKENS_OUT_PER_STEP,
                )
                _print_step(step, action, session.spent_usd)
                time.sleep(STEP_DELAY_S)
        except TripError as e:
            # Show the step that pushed us past the cap so the bar visibly fills.
            action = ROTATION[(step - 1) % len(ROTATION)]
            _print_step(step, action, session.spent_usd)
            _print_halt(session, step, e)


def _print_step(step: int, action: str, spent: float) -> None:
    color = _bar_color(spent, BUDGET_USD)
    bar = _bar(spent, BUDGET_USD)
    print(
        f"  step {step:>3}  "
        f"{DIM}{action:<48}{RESET}  "
        f"{color}[{bar}] ${spent:>5.2f}{RESET}"
    )


def _print_halt(session: Magicrails, step: int, e: TripError) -> None:
    avg_per_step = session.spent_usd / max(step, 1)
    # Project at a realistic agent pace (~one step / 10s), not demo pace,
    # over an 8-hour "ran overnight before anyone noticed" window.
    realistic_steps_per_hour = 360
    overnight_cost = avg_per_step * realistic_steps_per_hour * 8

    print()
    print(f"  {BOLD}{RED}🛑  HALT  🛑{RESET}")
    print(f"  {RED}{e.reason}{RESET}")
    print()
    print(f"  spent     : {BOLD}${session.spent_usd:.4f}{RESET}")
    print(f"  steps     : {BOLD}{step}{RESET}")
    print(f"  halted in : {BOLD}~{step * STEP_DELAY_S:.1f}s{RESET}")
    print()
    print(
        f"  {DIM}left running overnight at this cost-per-step,"
        f" the bill would be ~${overnight_cost:,.0f}.{RESET}"
    )
    print()
    print(f"  {GREEN}{BOLD}✓ saved by Magicrails — pip install magicrails{RESET}")
    print()


if __name__ == "__main__":
    main()

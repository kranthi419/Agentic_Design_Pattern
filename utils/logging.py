import time

from colorama import Fore, Style


def fancy_print(message: str) -> None:
    """
    Display a fancy print message.
    :param message: The message to display.
    """
    print(Style.BRIGHT + Fore.CYAN + f"\n{'=' * 50}")
    print(Fore.MAGENTA + f"{message}")
    print(Style.BRIGHT + Fore.CYAN + f"{'=' * 50}\n")
    time.sleep(0.5)


def fancy_step_tracker(step: int, total_steps: int) -> None:
    """
    Display a fancy step tracker for each iteration of the generation-reflection loop.
    :param step: The current step.
    :param total_steps: The total number of steps.
    """
    fancy_print(f"STEP {step + 1}/{total_steps}")


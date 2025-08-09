# utils/tools.py

import re

def clean_numbers(raw_numbers: list[str]) -> list[str]:
    """
    Cleans and validates a list of phone numbers:
    - Strips unwanted characters
    - Adds '+' if missing
    - Ensures valid international format
    - Deduplicates entries
    - Removes clearly invalid formats
    """
    cleaned = set()

    for num in raw_numbers:
        if not num:
            continue

        # Remove unwanted characters (spaces, dashes, parentheses)
        num = re.sub(r"[^\d+]", "", num)

        # Add + if missing
        if not num.startswith("+"):
            num = "+" + num

        # Ensure it's only digits after +
        if not re.fullmatch(r"\+\d{7,15}", num):
            continue  # Skip invalid formats

        cleaned.add(num)

    return list(cleaned)


def split_batches(numbers: list[str], batch_size: int = 10) -> list[list[str]]:
    """
    Splits list of numbers into batches of given size (default 10)
    """
    return [numbers[i:i + batch_size] for i in range(0, len(numbers), batch_size)]

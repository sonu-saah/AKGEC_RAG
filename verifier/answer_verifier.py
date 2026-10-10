
import re


def normalize_number(number):
    try:
        return float(number.replace(",", ""))
    except ValueError:
        return None


def extract_numbers(text):
    numbers = re.findall(r"\b\d[\d,]*(?:\.\d+)?\b", text)
    return {
        value
        for number in numbers
        if (value := normalize_number(number)) is not None
    }


def verify_numeric_claims(answer, context):
    context_numbers = extract_numbers(context)
    answer_numbers = extract_numbers(answer)
    unsupported_numbers = answer_numbers - context_numbers

    if unsupported_numbers:
        return False, unsupported_numbers

    return True, set()


def verify_answer(answer, context):
    answer_clean = answer.strip().lower()
    context_clean = context.strip()

    # An empty answer or missing evidence must not pass verification.
    if not answer_clean or not context_clean:
        return {
            "verified": False,
            "reason": "Answer or supporting context is empty.",
            "unsupported_numbers": []
        }

    # An abstention is not a verified factual answer.
    if any(phrase in answer_clean for phrase in (
        "i could not find this information",
        "i couldn't find this information",
        "information is not available",
        "i don't have enough information",
    )):
        return {
            "verified": False,
            "reason": "The system could not answer from the retrieved data.",
            "unsupported_numbers": []
        }

    is_valid, unsupported_numbers = verify_numeric_claims(
        answer, context
    )

    if not is_valid:
        return {
            "verified": False,
            "reason": "Answer contains numeric values not found in retrieved context.",
            "unsupported_numbers": sorted(unsupported_numbers)
        }

    return {
        "verified": True,
        "reason": "Numeric claims passed; non-numeric claims are not fully fact-checked.",
        "unsupported_numbers": []
    }


if __name__ == "__main__":
    print(verify_answer(
        "I could not find this information in the AKGEC data.",
        "Some unrelated AKGEC information."
    ))

    print(verify_answer(
        "The academic fee is Rs. 142,156.",
        "Academic Fee for 2026-27. Total 142156"
    ))

import re


def normalize_number(number):
    try:
        return float(number.replace(",", ""))
    except ValueError:
        return None


def extract_numbers(text):
    numbers = re.findall(r"\b\d[\d,]*(?:\.\d+)?\b", text)
    return {
        value
        for number in numbers
        if (value := normalize_number(number)) is not None
    }


def verify_numeric_claims(answer, context):
    context_numbers = extract_numbers(context)
    answer_numbers = extract_numbers(answer)
    unsupported_numbers = answer_numbers - context_numbers

    if unsupported_numbers:
        return False, unsupported_numbers

    return True, set()


def verify_answer(answer, context):
    answer_clean = answer.strip().lower()
    context_clean = context.strip()

    # An empty answer or missing evidence must not pass verification.
    if not answer_clean or not context_clean:
        return {
            "verified": False,
            "reason": "Answer or supporting context is empty.",
            "unsupported_numbers": []
        }

    # An abstention is not a verified factual answer.
    if any(phrase in answer_clean for phrase in (
        "i could not find this information",
        "i couldn't find this information",
        "information is not available",
        "i don't have enough information",
    )):
        return {
            "verified": False,
            "reason": "The system could not answer from the retrieved data.",
            "unsupported_numbers": []
        }

    is_valid, unsupported_numbers = verify_numeric_claims(
        answer, context
    )

    if not is_valid:
        return {
            "verified": False,
            "reason": "Answer contains numeric values not found in retrieved context.",
            "unsupported_numbers": sorted(unsupported_numbers)
        }

    return {
        "verified": True,
        "reason": "Numeric claims passed; non-numeric claims are not fully fact-checked.",
        "unsupported_numbers": []
    }


if __name__ == "__main__":
    print(verify_answer(
        "I could not find this information in the AKGEC data.",
        "Some unrelated AKGEC information."
    ))

    print(verify_answer(
        "The academic fee is Rs. 142,156.",
        "Academic Fee for 2026-27. Total 142156"
    ))

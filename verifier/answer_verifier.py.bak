import re

# 🔴 NIC Q&A IMPORTANT
# Convert numbers like 142,156.00 and 142156 into the same format.
def normalize_number(number):
    try:
        return float(number.replace(",", ""))
    except ValueError:
        return None


# Extract and normalize all numeric values from text.
def extract_numbers(text):
    numbers = re.findall(
        r"\b\d[\d,]*(?:\.\d+)?\b",
        text
    )

    normalized = set()

    for number in numbers:
        value = normalize_number(number)

        if value is not None:
            normalized.add(value)

    return normalized


# 🔴 NIC Q&A IMPORTANT
# Check whether numeric values in the answer exist in the retrieved context.
def verify_numeric_claims(answer, context):
    context_numbers = extract_numbers(context)
    answer_numbers = extract_numbers(answer)

    unsupported_numbers = answer_numbers - context_numbers

    if unsupported_numbers:
        return False, unsupported_numbers

    return True, set()


# Verify the generated answer against retrieved AKGEC context.
def verify_answer(answer, context):
    is_valid, unsupported_numbers = verify_numeric_claims(
        answer,
        context
    )

    if not is_valid:
        return {
            "verified": False,
            "reason": "Answer contains numeric values not found in retrieved context.",
            "unsupported_numbers": list(unsupported_numbers)
        }

    return {
        "verified": True,
        "reason": "Answer is supported by the retrieved context.",
        "unsupported_numbers": []
    }


# Test the verifier independently.
if __name__ == "__main__":
    answer = "The total academic fee is Rs. 142,156.00."

    context = """
    B.Tech 1st Year
    Academic Fee for 2026-27
    Total 142156
    """

    result = verify_answer(answer, context)

    print("\nANSWER VERIFICATION")
    print(result)
import re


# Checks whether important numeric values from the retrieved context
# are actually present in the generated answer.
def verify_numeric_claims(answer, context):
    context_numbers = set(
        re.findall(r"\b\d[\d,]*(?:\.\d+)?\b", context)
    )

    answer_numbers = set(
        re.findall(r"\b\d[\d,]*(?:\.\d+)?\b", answer)
    )

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

    result = verify_answer(
        answer,
        context
    )

    print("\nANSWER VERIFICATION")
    print(result)
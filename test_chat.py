from rag.answer_generator_v2_table_test import AnswerGenerator

ag = AnswerGenerator()

print("\nAKGEC RAG Chatbot Ready! (Type exit to stop)")

while True:
    q = input("\nAsk Question: ").strip()

    if q.lower() in ["exit", "quit"]:
        print("Chatbot stopped.")
        break

    if not q:
        continue

    try:
        result = ag.answer(q)
        print("\nANSWER:\n", result[0])
        print("\nSOURCES:\n", result[1])

    except Exception as e:
        print("\nError:", e)

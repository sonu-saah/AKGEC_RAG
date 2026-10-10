
import streamlit as st

st.set_page_config(
    page_title="AKGEC Chatbot",
    page_icon="🎓",
    layout="centered"
)

# ---------- UI ----------
st.title("🎓 AKGEC Chatbot")
st.caption("Ask questions about AKGEC courses, fees, placements and facilities.")

with st.sidebar:
    st.header("About")
    st.write("AKGEC information assistant using RAG.")
    if st.button("Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

if "messages" not in st.session_state:
    st.session_state.messages = []

# Show existing conversation
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

question = st.chat_input("Ask your question about AKGEC...")

if question:
    st.session_state.messages.append(
        {"role": "user", "content": question}
    )

    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Searching AKGEC information..."):
            try:
                # Import backend here so UI can still load if an import fails
                from rag.retriever import search, combine_results, rerank
                from llm.gemini import generate_answer
                from verifier.answer_verifier import verify_answer

                # Retrieve relevant documents
                search_output = search(question)
                vector_results = search_output[0]
                keyword_results = search_output[1]

                results = combine_results(
                    vector_results,
                    keyword_results
                )

                results = rerank(question, results)

                # Build context safely
                context_parts = []
                urls = []

                for result in results:
                    if not isinstance(result, dict):
                        continue

                    source = (
                        result.get("url")
                        or result.get("source")
                        or result.get("metadata", {}).get("url", "")
                        or "AKGEC"
                    )

                    text_content = (
                        result.get("text")
                        or result.get("content")
                        or result.get("page_content")
                        or ""
                    )

                    if text_content:
                        context_parts.append(
                            f"Source: {source}\n{text_content}"
                        )

                    if isinstance(source, str) and source.startswith("http"):
                        if source not in urls:
                            urls.append(source)

                context = "\n\n".join(context_parts)

                if not context.strip():
                    st.warning(
                        "No relevant information was retrieved. "
                        "Try asking the question differently."
                    )
                else:
                    answer = generate_answer(question, context)

                    if not answer:
                        answer = (
                            "Sorry, I could not generate an answer. "
                            "Please try again."
                        )

                    if not isinstance(answer, str):
                        answer = str(answer)

                    st.markdown(answer)

                    # Verification is optional; it should not hide the answer
                    try:
                        verification = verify_answer(answer, context)

                        if isinstance(verification, dict):
                            verified = verification.get("verified")
                            if verified is not None:
                                st.caption(
                                    "Numeric verification: "
                                    + (
                                        "Passed"
                                        if verified
                                        else "Needs review"
                                    )
                                )
                    except Exception:
                        st.caption("Answer verification was unavailable.")

                    if urls:
                        with st.expander("Sources"):
                            for url in urls[:5]:
                                st.markdown(f"- [{url}]({url})")

                    st.session_state.messages.append(
                        {"role": "assistant", "content": answer}
                    )

            except Exception as error:
                st.error("The chatbot encountered an error.")
                st.exception(error)

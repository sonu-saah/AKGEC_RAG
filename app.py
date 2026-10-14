
import streamlit as st

# Configure Streamlit page
st.set_page_config(
    page_title="AKGEC AI Chatbot",
    page_icon="🎓",
    layout="wide"
)

# Display chatbot heading
st.title("🎓 AKGEC AI Chatbot")
st.caption("AI-powered College Information Assistant using Hybrid RAG")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Load RAG backend functions
@st.cache_resource(show_spinner=False)
def load_backend():
    from rag.retriever import search, combine_results, rerank
    from llm.gemini import generate_answer
    return search, combine_results, rerank, generate_answer

# Display sidebar
with st.sidebar:
    st.header("AKGEC Chatbot")
    st.write("Ask about courses, admission, fees, placements and hostel.")

    if st.button("Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.caption("Powered by ChromaDB + BM25 + Gemini")

# Display previous messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

        if message.get("sources"):
            with st.expander("Sources"):
                for source in message["sources"]:
                    st.write(source)

# Accept user question
question = st.chat_input("Ask anything about AKGEC...")

if question:
    st.session_state.messages.append({
        "role": "user",
        "content": question
    })

    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        try:
            with st.spinner("Generating answer..."):

                # Load backend
                search, combine_results, rerank, generate_answer = load_backend()

                # Perform hybrid retrieval
                vector_results, keyword_results, _, _ = search(question)

                # Combine vector and keyword results
                combined_results = combine_results(
                    vector_results,
                    keyword_results
                )

                # Rerank retrieved documents
                results = rerank(question, combined_results)

                sources = []

                if not results:
                    answer = (
                        "Sorry, I could not find relevant "
                        "information in the AKGEC knowledge base."
                    )
                else:
                    # Build context from retrieved chunks
                    context_parts = []

                    for result in results:
                        context_parts.append(
                            f"Source: {result.get('source', '')}\n"
                            f"Page: {result.get('page', '')}\n"
                            f"Type: {result.get('type', '')}\n"
                            f"Content: {result.get('text', '')}"
                        )

                    context = "\n\n".join(context_parts)

                    # Generate answer using Gemini
                    answer = generate_answer(question, context)

                    # Collect unique source references
                    seen = set()

                    for result in results:
                        source = result.get("source", "")

                        if source and source not in seen:
                            sources.append(source)
                            seen.add(source)

            # Display generated answer
            st.markdown(str(answer))

            # Display retrieved sources
            if sources:
                with st.expander("📚 Sources"):
                    for index, source in enumerate(sources, 1):
                        st.write(f"{index}. {source}")

            # Save assistant response
            st.session_state.messages.append({
                "role": "assistant",
                "content": str(answer),
                "sources": sources
            })

        except Exception as error:
            st.error(f"Chatbot error: {error}")

# Display footer
st.caption("AKGEC RAG Chatbot | SentenceTransformers | ChromaDB | BM25 | Gemini")

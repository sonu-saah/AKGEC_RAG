import streamlit as st
from rag.answer_generator import AnswerGenerator

# Configure chatbot page.
st.set_page_config(
    page_title="AKGEC AI Assistant",
    page_icon="??",
    layout="centered"
)

st.title("?? AKGEC AI Assistant")
st.caption("Ask questions about AKGEC using verified college information.")

# Load RAG backend only once.
@st.cache_resource
def load_chatbot():
    return AnswerGenerator()

# Store conversation history.
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display previous messages.
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

        for url in message.get("sources", []):
            st.markdown(f"?? [Official Source]({url})")

# Accept text questions.
question = st.chat_input("Ask anything about AKGEC...")

if question:
    st.session_state.messages.append({
        "role": "user",
        "content": question
    })

    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Searching official AKGEC information..."):
            try:
                chatbot = load_chatbot()
                answer, sources = chatbot.answer(question)
            except Exception as error:
                st.error(f"Error: {error}")
                st.stop()

        st.markdown(answer)

        for url in sources:
            st.markdown(f"?? [Official Source]({url})")

    st.session_state.messages.append({
        "role": "assistant",
        "content": answer,
        "sources": sources
    })

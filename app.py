
import time
import os

os.environ["STREAMLIT_SERVER_FILE_WATCHER_TYPE"] = "none"

import sqlite3
import uuid
from datetime import datetime

import streamlit as st

# ---------------- SETTINGS ----------------
st.set_page_config(
    page_title="AKGEC Chatbot",
    page_icon="🎓",
    layout="wide"
)

DB_PATH = os.path.join(
    os.path.dirname(__file__),
    "chat_history.db"
)


# ---------------- DATABASE ----------------
def get_connection():
    return sqlite3.connect(DB_PATH)


def init_db():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS chats (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (chat_id) REFERENCES chats(id)
            )
        """)


def create_chat():
    chat_id = str(uuid.uuid4())
    now = datetime.now().isoformat(timespec="seconds")

    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO chats (id, title, created_at)
            VALUES (?, ?, ?)
            """,
            (chat_id, "New chat", now)
        )

    return chat_id


def get_chats():
    with get_connection() as conn:
        return conn.execute(
            """
            SELECT id, title
            FROM chats
            ORDER BY created_at DESC
            """
        ).fetchall()


def get_messages(chat_id):
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT role, content
            FROM messages
            WHERE chat_id = ?
            ORDER BY id
            """,
            (chat_id,)
        ).fetchall()

    return [
        {"role": role, "content": content}
        for role, content in rows
    ]


def save_message(chat_id, role, content):
    now = datetime.now().isoformat(timespec="seconds")

    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO messages
            (chat_id, role, content, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (chat_id, role, content, now)
        )

        if role == "user":
            row = conn.execute(
                "SELECT title FROM chats WHERE id = ?",
                (chat_id,)
            ).fetchone()

            if row and row[0] == "New chat":
                title = content.strip().replace("\n", " ")[:45]

                conn.execute(
                    """
                    UPDATE chats
                    SET title = ?
                    WHERE id = ?
                    """,
                    (title or "New chat", chat_id)
                )


init_db()


# ---------------- SESSION ----------------
if "chat_id" not in st.session_state:
    chats = get_chats()

    st.session_state.chat_id = (
        chats[0][0] if chats else create_chat()
    )


# ---------------- SIDEBAR ----------------
with st.sidebar:
    st.title("🎓 AKGEC Chat")

    if st.button(
        "＋ New chat",
        use_container_width=True
    ):
        st.session_state.chat_id = create_chat()
        st.rerun()

    st.divider()
    st.subheader("Chat history")

    chats = get_chats()

    for chat_id, title in chats:
        if st.button(
            title[:45],
            key=f"chat_{chat_id}",
            use_container_width=True
        ):
            st.session_state.chat_id = chat_id
            st.rerun()

    st.divider()
    st.caption("Conversations are saved locally.")


# ---------------- MAIN CHAT ----------------
st.title("🎓 AKGEC Chatbot")

st.caption(
    "Ask about courses, admissions, "
    "campus facilities and more."
)

chat_id = st.session_state.chat_id
messages = get_messages(chat_id)

for message in messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# ---------------- ASK QUESTION ----------------
question = st.chat_input(
    "Message AKGEC Chatbot..."
)

if question:

    save_message(chat_id, "user", question)

    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):

        with st.spinner(
            "Searching AKGEC data and generating answer..."
        ):

            try:
                from rag.retriever import (
                    search,
                    combine_results,
                    rerank
                )

                from llm.gemini import generate_answer

                # ---------------- RETRIEVAL TIMER ----------------
                retrieval_start = time.perf_counter()

                vector_results, keyword_results, _, _ = search(
                    question
                )

                results = combine_results(
                    vector_results,
                    keyword_results,
                    top_k=5
                )

                results = rerank(
                    question,
                    results
                )

                retrieval_time = (
                    time.perf_counter() - retrieval_start
                )

                # ---------------- BUILD CONTEXT ----------------
                context_parts = []
                urls = []

                for result in results:

                    if not isinstance(result, dict):
                        continue

                    metadata = result.get("metadata") or {}

                    source = (
                        result.get("url")
                        or result.get("source")
                        or metadata.get("url")
                        or ""
                    )

                    text_content = (
                        result.get("text")
                        or result.get("content")
                        or result.get("page_content")
                        or ""
                    )

                    if text_content:
                        context_parts.append(
                            f"Source: {source or 'AKGEC'}\n"
                            f"{text_content}"
                        )

                    if (
                        isinstance(source, str)
                        and source.startswith("http")
                        and source not in urls
                    ):
                        urls.append(source)

                context = "\n\n".join(context_parts)

                # ---------------- GEMINI TIMER ----------------
                gemini_start = time.perf_counter()

                answer = generate_answer(
                    question,
                    context
                )

                gemini_time = (
                    time.perf_counter() - gemini_start
                )

                if not answer:
                    answer = (
                        "Sorry, I could not generate an answer."
                    )

                if not isinstance(answer, str):
                    answer = str(answer)

                # ---------------- DISPLAY ANSWER ----------------
                st.markdown(answer)

                st.caption(
                    f"Retrieval: {retrieval_time:.2f}s | "
                    f"Gemini: {gemini_time:.2f}s | "
                    f"Total: {retrieval_time + gemini_time:.2f}s"
                )

                # ---------------- SOURCES ----------------
                if urls:
                    with st.expander("Sources"):
                        for url in urls[:5]:
                            st.markdown(
                                f"- [{url}]({url})"
                            )

                # ---------------- SAVE ANSWER ----------------
                save_message(
                    chat_id,
                    "assistant",
                    answer
                )

            except Exception as error:
                st.error(
                    "Something went wrong while "
                    "generating the answer."
                )

                st.exception(error)

                save_message(
                    chat_id,
                    "assistant",
                    f"Error: {error}"
                )

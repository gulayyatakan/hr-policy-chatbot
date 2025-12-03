import streamlit as st
import requests

# Adjust if your FastAPI runs on another host/port
BASE_URL = "http://localhost:8000"

st.set_page_config(page_title="HR RAG Chatbot", page_icon="💬", layout="centered")

st.title("HR RAG Chatbot 💬")
st.caption("Answers based on your HR policy markdown files")

# --- Session state ---
if "messages" not in st.session_state:
    # each message: {role: "user"/"assistant", content: str, sources: optional[list]}
    st.session_state.messages = []


# --- Render chat history ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        # show sources below assistant answers
        if msg["role"] == "assistant" and msg.get("sources"):
            with st.expander("Sources used"):
                for s in msg["sources"]:
                    src = s.get("source", "unknown")
                    idx = s.get("chunk_index", "?")
                    st.write(f"- **{src}** (chunk {idx})")


# --- Chat input ---
prompt = st.chat_input("Ask a question about HR policies…")
if prompt:
    # 1) Show user message
    st.session_state.messages.append(
        {"role": "user", "content": prompt, "sources": None}
    )
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2) Call backend /chat endpoint
    with st.chat_message("assistant"):
        placeholder = st.empty()
        placeholder.markdown("_Thinking…_")

        try:
            res = requests.post(
                f"{BASE_URL}/chat",
                json={"question": prompt},
                timeout=60,
            )
            res.raise_for_status()
            data = res.json()

            answer = data.get("answer", "")
            sources = data.get("sources", []) or []

            # show final answer
            placeholder.markdown(answer)

        except Exception as e:
            answer = f"❌ Error contacting backend: `{e}`"
            sources = []
            placeholder.error(answer)

    # 3) Save assistant message in history
    st.session_state.messages.append(
        {"role": "assistant", "content": answer, "sources": sources}
    )

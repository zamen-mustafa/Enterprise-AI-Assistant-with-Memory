import streamlit as st

from app.assistant import EnterpriseAssistant
from app.config import get_settings
from app.documents import extract_text
from app.logging import configure_logging
from app.security import new_id, safe_filename

configure_logging(get_settings().log_level)
st.set_page_config(page_title="Enterprise AI Assistant", page_icon="🤝", layout="wide")

@st.cache_resource
def service():
    return EnterpriseAssistant(get_settings())

assistant = service()
if "user_id" not in st.session_state:
    st.session_state.user_id = new_id()
if "session_id" not in st.session_state:
    st.session_state.session_id = new_id()
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []

st.title("Enterprise AI Assistant")
st.caption("Intelligent conversations with persistent memory and knowledge retrieval")
with st.sidebar:
    st.subheader("Session")
    st.text_input("User ID", key="user_id")

    if st.button("＋ New chat", use_container_width=True):
        # Create a new conversation while keeping the same user memory.
        st.session_state.session_id = new_id()
        st.session_state.chat_messages = []
        st.rerun()

    st.caption("New chat starts a separate conversation but keeps your saved memory.")
    upload = st.file_uploader("Upload knowledge", type=["txt", "md", "pdf", "docx"])
    if upload and st.button("Index document"):
        try:
            if upload.size > get_settings().max_upload_mb * 1024 * 1024:
                raise ValueError("File is too large")
            text = extract_text(safe_filename(upload.name), upload.getvalue())
            if not text.strip():
                raise ValueError("No readable text found")
            chunks = assistant.vectors.add_document(new_id(), upload.name, text)
            st.success(f"Indexed {chunks} chunks")
        except Exception as exc:
            st.error(str(exc))

for message in st.session_state.chat_messages:
    st.chat_message(message["role"]).write(message["content"])

if prompt := st.chat_input("Ask about your work or uploaded knowledge"):
    st.session_state.chat_messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)
    with st.chat_message("assistant"):
        try:
            response = assistant.ask(st.session_state.user_id, st.session_state.session_id, prompt)
            # Stream output through Streamlit while the graph keeps persistence/citations intact.
            st.write_stream(iter(response.answer.splitlines(keepends=True)))
            st.session_state.chat_messages.append({"role": "assistant", "content": response.answer})
            if response.citations:
                st.caption("Sources")
                for citation in response.citations:
                    st.caption(f"{citation.source}, chunk {citation.chunk_index} (score {citation.score}) — {citation.excerpt[:180]}")
        except Exception as exc:
            st.error(f"Request failed: {exc}")

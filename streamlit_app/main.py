import os

import requests
import streamlit as st


API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")

st.set_page_config(page_title="Chatbot ISI", layout="wide")
st.title("Chatbot IA ISI")


def api_url(path: str) -> str:
    return f"{API_BASE_URL}{path}"


with st.sidebar:
    st.header("Documents")
    files = st.file_uploader(
        "Ajouter des PDF",
        type=["pdf"],
        accept_multiple_files=True,
    )

    if st.button("Indexer", type="primary", disabled=not files):
        multipart_files = [
            ("files", (file.name, file.getvalue(), "application/pdf"))
            for file in files or []
        ]
        with st.spinner("Indexation en cours..."):
            response = requests.post(api_url("/documents/upload"), files=multipart_files, timeout=300)
        if response.ok:
            payload = response.json()
            st.success(
                f"{payload['uploaded_count']} document(s) ajoute(s), "
                f"{payload['duplicate_count']} doublon(s)."
            )
        else:
            st.error(response.json().get("detail", response.text))

    try:
        documents_response = requests.get(api_url("/documents"), timeout=20)
        if documents_response.ok:
            for document in documents_response.json():
                st.caption(
                    f"{document['filename']} | {document['status']} | "
                    f"{document['chunk_count']} chunks"
                )
        else:
            st.warning("Impossible de charger la liste des documents.")
    except requests.RequestException:
        st.warning("API indisponible.")


question = st.chat_input("Pose une question sur les documents ISI")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Recherche dans les documents..."):
            try:
                response = requests.post(
                    api_url("/chat/ask"),
                    json={"question": question},
                    timeout=180,
                )
            except requests.RequestException as exc:
                st.error(f"API indisponible: {exc}")
            else:
                if response.ok:
                    payload = response.json()
                    answer = payload["answer"]
                    st.markdown(answer)

                    if payload["sources"]:
                        with st.expander("Sources utilisees"):
                            for source in payload["sources"]:
                                st.markdown(
                                    f"**{source['document_name']}** "
                                    f"(page {source['page_number'] or '?'}, "
                                    f"score {source['score']})"
                                )
                                st.caption(source["excerpt"])

                    st.session_state.messages.append(
                        {"role": "assistant", "content": answer}
                    )
                else:
                    st.error(response.json().get("detail", response.text))

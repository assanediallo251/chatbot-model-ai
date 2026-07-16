import os

import requests
import streamlit as st

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")

st.set_page_config(page_title="Chatbot ISI", layout="wide")
st.markdown(
    """
    <style>
    [data-testid="stSidebar"] {
        background: #f8fafc;
        border-right: 1px solid #e5e7eb;
    }

    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        letter-spacing: 0;
    }

    [data-testid="stSidebar"] [data-testid="stFileUploader"] {
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        padding: 0.85rem;
    }

    [data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] {
        border: 1px dashed #cbd5e1;
        border-radius: 8px;
        background: #f8fafc;
    }

    [data-testid="stSidebar"] .stButton > button {
        width: 100%;
        border-radius: 8px;
        font-weight: 600;
    }

    .sidebar-kicker {
        color: #64748b;
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0.04em;
        margin: 0 0 0.2rem;
        text-transform: uppercase;
    }

    .sidebar-title {
        color: #0f172a;
        font-size: 1.12rem;
        font-weight: 750;
        margin: 0 0 0.9rem;
    }

    .sidebar-section-label {
        color: #334155;
        font-size: 0.86rem;
        font-weight: 700;
        margin: 1.15rem 0 0.45rem;
    }

    .doc-row {
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        margin-bottom: 0.55rem;
        padding: 0.65rem 0.72rem;
    }

    .doc-name {
        color: #111827;
        font-size: 0.88rem;
        font-weight: 650;
        overflow-wrap: anywhere;
    }

    .doc-meta {
        align-items: center;
        color: #64748b;
        display: flex;
        font-size: 0.75rem;
        gap: 0.45rem;
        margin-top: 0.35rem;
    }

    .status-dot {
        border-radius: 999px;
        display: inline-block;
        height: 0.5rem;
        width: 0.5rem;
    }

    .status-indexed { background: #16a34a; }
    .status-processing { background: #f59e0b; }
    .status-failed { background: #dc2626; }
    .status-default { background: #94a3b8; }

    .sidebar-empty,
    .sidebar-state {
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        color: #64748b;
        font-size: 0.82rem;
        line-height: 1.4;
        padding: 0.7rem 0.75rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)
st.title("Chatbot IA ISI")


def api_url(path: str) -> str:
    return f"{API_BASE_URL}{path}"


def status_class(status: str) -> str:
    return {
        "indexed": "status-indexed",
        "processing": "status-processing",
        "failed": "status-failed",
    }.get(status, "status-default")


def render_document(document: dict) -> None:
    status = document["status"]
    page_label = "chunk" if document["chunk_count"] == 1 else "chunks"
    st.markdown(
        f"""
        <div class="doc-row">
            <div class="doc-name">{document["filename"]}</div>
            <div class="doc-meta">
                <span class="status-dot {status_class(status)}"></span>
                <span>{status}</span>
                <span>•</span>
                <span>{document["chunk_count"]} {page_label}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


with st.sidebar:
    st.markdown('<p class="sidebar-kicker">ISI Chatbot</p>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-title">Base documentaire</div>', unsafe_allow_html=True)

    st.markdown('<div class="sidebar-section-label">Importer</div>', unsafe_allow_html=True)
    files = st.file_uploader(
        "Fichiers PDF",
        type=["pdf"],
        accept_multiple_files=True,
        label_visibility="collapsed",
    )

    if st.button("Indexer", type="primary", disabled=not files):
        multipart_files = [
            ("files", (file.name, file.getvalue(), "application/pdf"))
            for file in files or []
        ]
        with st.spinner("Indexation en cours..."):
            response = requests.post(
                api_url("/documents/upload"),
                files=multipart_files,
                timeout=300,
            )
        if response.ok:
            payload = response.json()
            st.success(
                f"{payload['uploaded_count']} document(s) ajoute(s), "
                f"{payload['duplicate_count']} doublon(s)."
            )
        else:
            st.error(response.json().get("detail", response.text))

    st.markdown('<div class="sidebar-section-label">Documents</div>', unsafe_allow_html=True)
    try:
        documents_response = requests.get(api_url("/documents"), timeout=20)
        if documents_response.ok:
            documents = documents_response.json()
            if documents:
                for document in documents:
                    render_document(document)
            else:
                st.markdown(
                    '<div class="sidebar-empty">Aucun document indexe.</div>',
                    unsafe_allow_html=True,
                )
        else:
            st.markdown(
                '<div class="sidebar-state">'
                "Liste indisponible. Verifie que l API est lancee."
                "</div>",
                unsafe_allow_html=True,
            )
    except requests.RequestException:
        st.markdown(
            f'<div class="sidebar-state">API indisponible<br>{API_BASE_URL}</div>',
            unsafe_allow_html=True,
        )


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

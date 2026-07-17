import os
from html import escape

import requests
import streamlit as st

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")
MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB") or "20")
LUCIDE_FILE_UP_ICON_DATA_URI = (
    "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' "
    "width='46' height='46' viewBox='0 0 24 24' fill='none' "
    "stroke='%230f766e' stroke-width='2' stroke-linecap='round' "
    "stroke-linejoin='round'%3E%3Cpath d='M6 22a2 2 0 0 1-2-2V4a2 "
    "2 0 0 1 2-2h8a2.4 2.4 0 0 1 1.704.706l3.588 3.588A2.4 2.4 0 "
    "0 1 20 8v12a2 2 0 0 1-2 2z'/%3E%3Cpath d='M14 2v5a1 1 0 0 0 "
    "1 1h5'/%3E%3Cpath d='M12 12v6'/%3E%3Cpath d='m15 15-3-3-3 "
    "3'/%3E%3C/svg%3E"
)

st.set_page_config(page_title="Chatbot ISI", layout="wide")
st.markdown(
    """
    <style>
    [data-testid="stSidebar"] {
        --sidebar-bg: #f6f8fb;
        --sidebar-border: #dbe3ef;
        --sidebar-card: #ffffff;
        --sidebar-muted: #64748b;
        --sidebar-text: #0f172a;
        --sidebar-accent: #0f766e;
        --sidebar-accent-dark: #115e59;
        background: var(--sidebar-bg);
        border-right: 1px solid #e2e8f0;
    }

    [data-testid="stSidebar"] > div:first-child {
        padding: 1.55rem 1.1rem 1.15rem;
    }

    [data-testid="stSidebar"] * {
        letter-spacing: 0;
    }

    .sidebar-brand {
        align-items: center;
        display: flex;
        gap: 0.78rem;
        margin-bottom: 0.5rem;
    }

    .sidebar-brand-mark {
        align-items: center;
        background: #0f172a;
        border: 1px solid #1e293b;
        border-radius: 8px;
        color: #ffffff;
        display: inline-flex;
        flex: 0 0 auto;
        font-size: 0.72rem;
        font-weight: 800;
        height: 2.45rem;
        justify-content: center;
        width: 2.45rem;
    }

    .sidebar-kicker {
        color: var(--sidebar-muted);
        font-size: 0.72rem;
        font-weight: 750;
        margin: 0 0 0.12rem;
        text-transform: uppercase;
    }

    .sidebar-title {
        color: var(--sidebar-text);
        font-size: 1.12rem;
        font-weight: 780;
        line-height: 1.15;
        margin: 0;
    }

    .sidebar-section-heading {
        align-items: center;
        color: #1e293b;
        display: flex;
        font-size: 0.84rem;
        font-weight: 780;
        justify-content: space-between;
        margin: 1.08rem 0 0.5rem;
    }

    .sidebar-section-note {
        color: var(--sidebar-muted);
        font-size: 0.7rem;
        font-weight: 700;
        line-height: 1.2;
    }

    [data-testid="stSidebar"] [data-testid="stFileUploader"] {
        background: var(--sidebar-card);
        border: 1px solid var(--sidebar-border);
        border-radius: 8px;
        box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
        padding: 0.68rem;
    }

    [data-testid="stSidebar"] [data-testid="stFileUploader"] section {
        padding: 0;
    }

    [data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] {
        align-items: center;
        background:
            linear-gradient(180deg, rgba(240, 253, 250, 0.96), rgba(248, 250, 252, 1));
        border: 1px dashed #5eead4;
        border-radius: 8px;
        box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.92);
        display: flex;
        flex-direction: column;
        justify-content: center;
        min-height: 13rem;
        padding: 1.15rem 0.85rem;
        position: relative;
        text-align: center;
    }

    [data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"]:hover {
        background:
            linear-gradient(180deg, rgba(204, 251, 241, 0.9), rgba(248, 250, 252, 1));
        border-color: var(--sidebar-accent);
    }

    [data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"]::before {
        background-color: #ffffff;
        background-image: url("__LUCIDE_FILE_UP_ICON__");
        background-position: center;
        background-repeat: no-repeat;
        background-size: 2.35rem;
        border: 1px solid #ccfbf1;
        border-radius: 14px;
        box-shadow: 0 10px 22px rgba(15, 23, 42, 0.08);
        content: "";
        display: block;
        height: 4.35rem;
        margin-bottom: 0.78rem;
        order: 1;
        width: 4.35rem;
    }

    [data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"]::after {
        color: var(--sidebar-muted);
        content: "Documents PDF\\AGlissez-deposez vos fichiers ici";
        display: block;
        font-size: 0.76rem;
        font-weight: 650;
        line-height: 1.45;
        margin: 0;
        order: 2;
        white-space: pre-line;
    }

    [data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] > div {
        align-items: center;
        display: flex;
        flex-direction: column;
        gap: 0.2rem;
        justify-content: center;
        order: 3;
        text-align: center;
        width: 100%;
    }

    [data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] svg {
        display: none;
    }

    [data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] p {
        display: none;
    }

    [data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] small {
        display: none;
    }

    [data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] button {
        display: none;
    }

    [data-testid="stSidebar"] [data-testid="stFileUploader"] small {
        color: #64748b;
        font-size: 0.76rem;
        line-height: 1.35;
    }

    [data-testid="stSidebar"] .stButton > button {
        background: #0f172a;
        border: 1px solid #0f172a;
        border-radius: 8px;
        color: #ffffff;
        font-weight: 750;
        min-height: 2.75rem;
        width: 100%;
    }

    [data-testid="stSidebar"] .stButton > button:hover {
        background: #1e293b;
        border-color: #1e293b;
        color: #ffffff;
    }

    [data-testid="stSidebar"] .stButton > button:disabled,
    [data-testid="stSidebar"] .stButton > button:disabled:hover {
        background: #e2e8f0;
        border-color: #e2e8f0;
        color: #94a3b8;
    }

    [data-testid="stSidebar"] .stAlert {
        border-radius: 8px;
    }

    .upload-selection {
        margin-top: 0.78rem;
    }

    .upload-selection-head {
        align-items: center;
        color: #334155;
        display: flex;
        font-size: 0.78rem;
        font-weight: 750;
        justify-content: space-between;
        margin-bottom: 0.5rem;
    }

    .upload-selection-count {
        color: var(--sidebar-muted);
        font-size: 0.7rem;
        font-weight: 700;
    }

    .upload-summary {
        background: var(--sidebar-card);
        border: 1px solid var(--sidebar-border);
        border-radius: 8px;
        box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
        display: grid;
        gap: 0.55rem;
        grid-template-columns: 1fr 1fr;
        margin-bottom: 0.55rem;
        padding: 0.68rem;
    }

    .upload-stat-value {
        color: var(--sidebar-text);
        display: block;
        font-size: 0.96rem;
        font-weight: 780;
        line-height: 1.1;
    }

    .upload-stat-label {
        color: var(--sidebar-muted);
        display: block;
        font-size: 0.72rem;
        margin-top: 0.18rem;
    }

    .upload-file-row {
        align-items: center;
        background: var(--sidebar-card);
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        display: flex;
        gap: 0.62rem;
        margin-bottom: 0.45rem;
        padding: 0.62rem 0.68rem;
    }

    .upload-file-badge {
        align-items: center;
        background: #ecfeff;
        border: 1px solid #a5f3fc;
        border-radius: 7px;
        color: #155e75;
        display: inline-flex;
        flex: 0 0 auto;
        font-size: 0.68rem;
        font-weight: 800;
        height: 1.65rem;
        justify-content: center;
        width: 2.3rem;
    }

    .upload-file-main {
        min-width: 0;
    }

    .upload-file-name {
        color: var(--sidebar-text);
        font-size: 0.82rem;
        font-weight: 650;
        line-height: 1.25;
        overflow-wrap: anywhere;
    }

    .upload-file-meta {
        color: var(--sidebar-muted);
        font-size: 0.72rem;
        margin-top: 0.16rem;
    }

    .sidebar-divider {
        border-top: 1px solid #e2e8f0;
        margin: 1.15rem 0 0;
    }

    .doc-overview {
        background: rgba(255, 255, 255, 0.72);
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        display: grid;
        gap: 0.5rem;
        grid-template-columns: repeat(3, 1fr);
        margin-bottom: 0.62rem;
        padding: 0.62rem;
    }

    .doc-overview-value {
        color: var(--sidebar-text);
        display: block;
        font-size: 0.92rem;
        font-weight: 780;
        line-height: 1.1;
    }

    .doc-overview-label {
        color: var(--sidebar-muted);
        display: block;
        font-size: 0.68rem;
        margin-top: 0.15rem;
    }

    .doc-row {
        background: var(--sidebar-card);
        border: 1px solid var(--sidebar-border);
        border-left: 3px solid #94a3b8;
        border-radius: 8px;
        box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
        margin-bottom: 0.55rem;
        padding: 0.68rem 0.72rem;
    }

    .doc-row-indexed { border-left-color: #16a34a; }
    .doc-row-processing { border-left-color: #f59e0b; }
    .doc-row-failed { border-left-color: #dc2626; }

    .doc-name {
        color: var(--sidebar-text);
        font-size: 0.88rem;
        font-weight: 650;
        line-height: 1.28;
        overflow-wrap: anywhere;
    }

    .doc-meta {
        align-items: center;
        color: var(--sidebar-muted);
        display: flex;
        font-size: 0.75rem;
        gap: 0.45rem;
        margin-top: 0.35rem;
        flex-wrap: wrap;
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

    .doc-error {
        color: #991b1b;
        font-size: 0.72rem;
        line-height: 1.35;
        margin-top: 0.35rem;
        overflow-wrap: anywhere;
    }

    .sidebar-empty,
    .sidebar-state {
        background: var(--sidebar-card);
        border: 1px solid var(--sidebar-border);
        border-radius: 8px;
        color: var(--sidebar-muted);
        font-size: 0.82rem;
        line-height: 1.4;
        padding: 0.7rem 0.75rem;
        box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
    }

    .sidebar-state strong {
        color: var(--sidebar-text);
        display: block;
        font-size: 0.82rem;
        margin-bottom: 0.18rem;
    }
    </style>
    """.replace("__LUCIDE_FILE_UP_ICON__", LUCIDE_FILE_UP_ICON_DATA_URI),
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


def status_key(status: str) -> str:
    return status if status in {"indexed", "processing", "failed"} else "default"


def status_label(status: str) -> str:
    return {
        "indexed": "Indexe",
        "processing": "Traitement",
        "failed": "Erreur",
    }.get(status, status)


def format_file_size(size_bytes: int) -> str:
    if size_bytes >= 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} Mo"
    if size_bytes >= 1024:
        return f"{size_bytes / 1024:.0f} Ko"
    return f"{size_bytes} o"


def uploaded_file_size(file) -> int:
    size = getattr(file, "size", None)
    if size is not None:
        return int(size)
    return len(file.getbuffer())


def render_upload_selection(files) -> None:
    if not files:
        return

    total_size = sum(uploaded_file_size(file) for file in files)
    file_rows = "\n".join(
        f"""
        <div class="upload-file-row">
            <span class="upload-file-badge">PDF</span>
            <div class="upload-file-main">
                <div class="upload-file-name">{escape(file.name)}</div>
                <div class="upload-file-meta">{format_file_size(uploaded_file_size(file))}</div>
            </div>
        </div>
        """
        for file in files
    )

    st.markdown(
        f"""
        <div class="upload-selection">
            <div class="upload-selection-head">
                <span>Selection prete</span>
                <span class="upload-selection-count">{len(files)} fichier(s)</span>
            </div>
            <div class="upload-summary">
                <div>
                    <span class="upload-stat-value">{len(files)}</span>
                    <span class="upload-stat-label">PDF</span>
                </div>
                <div>
                    <span class="upload-stat-value">{format_file_size(total_size)}</span>
                    <span class="upload-stat-label">Volume total</span>
                </div>
            </div>
            <div class="upload-file-list">
                {file_rows}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def response_error_message(response: requests.Response) -> str:
    try:
        payload = response.json()
    except ValueError:
        return response.text
    return payload.get("detail", response.text)


def document_counts(documents: list[dict]) -> dict[str, int]:
    counts = {"total": len(documents), "indexed": 0, "processing": 0, "failed": 0}
    for document in documents:
        status = document.get("status")
        if status in counts:
            counts[status] += 1
    return counts


def render_documents_overview(documents: list[dict]) -> None:
    counts = document_counts(documents)
    st.markdown(
        f"""
        <div class="doc-overview">
            <div>
                <span class="doc-overview-value">{counts["total"]}</span>
                <span class="doc-overview-label">Total</span>
            </div>
            <div>
                <span class="doc-overview-value">{counts["indexed"]}</span>
                <span class="doc-overview-label">Prets</span>
            </div>
            <div>
                <span class="doc-overview-value">{counts["processing"]}</span>
                <span class="doc-overview-label">En cours</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_document(document: dict) -> None:
    status = document["status"]
    page_label = "chunk" if document["chunk_count"] == 1 else "chunks"
    error_html = ""
    if document.get("error_message"):
        error_html = f'<div class="doc-error">{escape(document["error_message"])}</div>'

    st.markdown(
        f"""
        <div class="doc-row doc-row-{status_key(status)}">
            <div class="doc-name">{escape(document["filename"])}</div>
            <div class="doc-meta">
                <span class="status-dot {status_class(status)}"></span>
                <span>{escape(status_label(status))}</span>
                <span>&middot;</span>
                <span>{document["chunk_count"]} {page_label}</span>
            </div>
            {error_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


with st.sidebar:
    st.markdown(
        """
        <div class="sidebar-brand">
            <div class="sidebar-brand-mark">ISI</div>
            <div>
                <p class="sidebar-kicker">Chatbot IA</p>
                <div class="sidebar-title">Base documentaire</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="sidebar-section-heading">
            <span>Importer</span>
            <span class="sidebar-section-note">PDF &middot; {MAX_UPLOAD_MB} Mo max</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    files = st.file_uploader(
        "Fichiers PDF",
        type=["pdf"],
        accept_multiple_files=True,
        label_visibility="collapsed",
    )
    render_upload_selection(files)

    if st.button("Indexer les documents", type="primary", disabled=not files):
        multipart_files = [
            ("files", (file.name, file.getvalue(), "application/pdf"))
            for file in files or []
        ]
        with st.spinner("Envoi et indexation en cours..."):
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
            st.error(response_error_message(response))

    st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sidebar-section-heading"><span>Documents</span></div>',
        unsafe_allow_html=True,
    )
    try:
        documents_response = requests.get(api_url("/documents"), timeout=20)
        if documents_response.ok:
            documents = documents_response.json()
            if documents:
                render_documents_overview(documents)
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
                "<strong>Documents indisponibles</strong>"
                "Verifie que l'API est lancee."
                "</div>",
                unsafe_allow_html=True,
            )
    except requests.RequestException:
        st.markdown(
            (
                '<div class="sidebar-state"><strong>API indisponible</strong>'
                f"{escape(API_BASE_URL)}</div>"
            ),
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
                                location = (
                                    f"page {source['page_number']}"
                                    if source["page_number"]
                                    else "source web"
                                    if source["document_name"].startswith("Web -")
                                    else "page ?"
                                )
                                st.markdown(
                                    f"**{source['document_name']}** "
                                    f"({location}, "
                                    f"score {source['score']})"
                                )
                                st.caption(source["excerpt"])

                    st.session_state.messages.append(
                        {"role": "assistant", "content": answer}
                    )
                else:
                    st.error(response_error_message(response))

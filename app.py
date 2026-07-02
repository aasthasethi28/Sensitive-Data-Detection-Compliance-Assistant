import streamlit as st

from modules.document_manager import DocumentManager
from modules.qa import DocumentQA
from modules.dashboard import DashboardManager
from modules.analytics import Analytics

# PAGE CONFIG

st.set_page_config(
    page_title="Enterprise AI Compliance Assistant",
    page_icon="🔒",
    layout="wide"
)

# SESSION STATE

if "documents" not in st.session_state:
    st.session_state.documents = []

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# TITLE

st.title("🔒 Enterprise AI Compliance Assistant")

st.markdown("""
### AI Powered Sensitive Data Detection & Compliance Platform

Upload one or more documents and automatically:

- 📄 Extract text
- 🔍 Detect sensitive information
- 🚨 Assess document risk
- 📋 Generate AI compliance reports
- 💬 Chat with your documents using RAG
""")

st.info(
    "Supported formats: PDF • TXT • CSV • DOCX"
)

# SIDEBAR

st.sidebar.title("📂 Uploaded Documents")

if st.session_state.documents:

    for doc in st.session_state.documents:

        st.sidebar.success(doc["filename"])

else:

    st.sidebar.info(
        "No documents uploaded."
    )

st.sidebar.divider()

if st.sidebar.button("🗑 Clear Session"):

    st.session_state.documents = []

    st.session_state.chat_history = []

    st.rerun()

# FILE UPLOAD

uploaded_files = st.file_uploader(

    "Upload Documents",

    type=["pdf", "txt", "csv", "docx"],

    accept_multiple_files=True

)

# DOCUMENT PROCESSING

if uploaded_files and not st.session_state.documents:

    with st.spinner("📄 Processing uploaded documents..."):

        manager = DocumentManager()

        st.session_state.documents = manager.process_documents(
            uploaded_files
        )

# DASHBOARD

if st.session_state.documents:

    stats = DashboardManager.get_statistics(
        st.session_state.documents
    )

    st.divider()

    st.header("📊 Enterprise Dashboard")

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        st.metric(
            "📄 Documents",
            stats["total_documents"]
        )

    with col2:

        st.metric(
            "🔴 High Risk",
            stats["high_risk"]
        )

    with col3:

        st.metric(
            "🟡 Medium Risk",
            stats["medium_risk"]
        )

    with col4:

        st.metric(
            "🟢 Low Risk",
            stats["low_risk"]
        )

    st.markdown("---")

    st.subheader("📈 Analytics Dashboard")

    left, right = st.columns(2)

    with left:

        st.plotly_chart(
            Analytics.risk_distribution(stats),
            use_container_width=True
        )

    with right:

        st.plotly_chart(
            Analytics.sensitive_data_distribution(stats),
            use_container_width=True
        )

    st.divider()

# DOCUMENTS

if st.session_state.documents:

    st.header("📄 Uploaded Documents")

    for doc in st.session_state.documents:

        with st.expander(
            f"📄 {doc['filename']}",
            expanded=True
        ):

            # Extracted Text

            st.subheader("📄 Extracted Text")

            st.text_area(
                "Document Content",
                doc["text"],
                height=250,
                key=f"text_{doc['filename']}"
            )

            # Sensitive Data

            st.subheader("🔍 Sensitive Data Detected")

            st.json(doc["detections"])

            # Risk

            st.subheader("🚨 Risk Assessment")

            c1, c2 = st.columns(2)

            with c1:

                st.metric(
                    "Risk Level",
                    doc["risk"]["risk_level"]
                )

            with c2:

                st.metric(
                    "Risk Score",
                    doc["risk"]["score"]
                )

            # Compliance Report

            st.subheader("📋 AI Compliance Report")

            st.markdown(doc["report"])

# ENTERPRISE AI CHATBOT

if st.session_state.documents:

    st.divider()

    st.header("🤖 Enterprise AI Assistant")

    st.write(
        "Ask questions about any uploaded document."
    )

    selected_filename = st.selectbox(

        "Choose Document",

        [
            doc["filename"]

            for doc in st.session_state.documents
        ]

    )

    selected_doc = next(

        doc

        for doc in st.session_state.documents

        if doc["filename"] == selected_filename

    )

    question = st.text_input(

        "Ask anything about this document..."

    )

    if st.button("🚀 Ask AI"):

        if question.strip():

            with st.spinner(
                "🤖 Thinking..."
            ):

                answer = DocumentQA.ask(

                    question,

                    selected_doc

                )

            st.session_state.chat_history.append(

                {

                    "document": selected_filename,

                    "question": question,

                    "answer": answer

                }

            )

# CHAT HISTORY

if st.session_state.chat_history:

    st.divider()

    st.header("💬 Conversation")

    for chat in reversed(
        st.session_state.chat_history
    ):

        st.info(
            f"📄 {chat['document']}"
        )

        st.markdown(

            f"**🧑 You:** {chat['question']}"

        )

        st.markdown(

            f"**🤖 AI:** {chat['answer']}"

        )

        st.divider()

# FOOTER

st.divider()

st.caption(
    "Enterprise AI Compliance Assistant | "
    "Built using Streamlit • FAISS • Gemini • Python"
)
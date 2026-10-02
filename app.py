"""
Streamlit Web Application for LPL AI Assistant
"""
import streamlit as st
from rag_engine import RAGEngine, Config

st.set_page_config(
    page_title="LPL AI Assistant",
    page_icon="🤖",
    layout="wide"
)

@st.cache_resource
def get_rag_engine():
    return RAGEngine()


def main():
    st.title("🤖 LPL AI Assistant")
    st.markdown("Ask questions about company documents and get answers with source citations.")

    with st.sidebar:
        st.header("About")
        backend = "OpenSearch" if Config.use_opensearch() else "FAISS (local)"
        st.markdown(f"""
        **Powered by:**
        - AWS Bedrock (Claude Sonnet 4.5)
        - {backend} vector search
        - Titan Embeddings
        """)

        st.divider()

        if st.button("Clear chat"):
            st.session_state.messages = []
            st.rerun()

        st.divider()
        st.caption("LPL Financial AI Hackathon 2025")

    if 'messages' not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message.get("sources"):
                with st.expander(f"📎 {len(message['sources'])} sources"):
                    for i, source in enumerate(message['sources'], 1):
                        st.markdown(f"**{i}. {source['source_file']}** (Page {source['page_number']})")
                        st.caption(source['text'][:300] + ("..." if len(source['text']) > 300 else ""))
                        st.divider()

    if prompt := st.chat_input("Ask a question about company documents..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Searching documents..."):
                try:
                    rag = get_rag_engine()
                    result = rag.query(prompt)

                    st.markdown(result['answer'])

                    if result['sources']:
                        with st.expander(f"📎 {len(result['sources'])} sources"):
                            for i, source in enumerate(result['sources'], 1):
                                st.markdown(f"**{i}. {source['source_file']}** (Page {source['page_number']})")
                                st.caption(source['text'][:300] + ("..." if len(source['text']) > 300 else ""))
                                st.divider()

                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": result['answer'],
                        "sources": result['sources']
                    })

                except Exception as e:
                    error_msg = f"Error: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": error_msg
                    })

if __name__ == "__main__":
    main()

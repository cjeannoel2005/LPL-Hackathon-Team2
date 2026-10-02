"""
Streamlit Web Application for LPL AI Assistant
"""
import streamlit as st
from rag_engine import RAGEngine, Config

# Page config
st.set_page_config(
    page_title="LPL AI Assistant",
    page_icon="🤖",
    layout="wide"
)

# Initialize RAG engine (cached)
@st.cache_resource
def get_rag_engine():
    return RAGEngine()

# Main app
def main():
    st.title("🤖 LPL AI Assistant")
    st.markdown("Ask questions about company documents and get answers with source citations")
    
    # Sidebar
    with st.sidebar:
        st.header("ℹ️ About")
        st.markdown("""
        This AI assistant searches through LPL documents 
        and provides synthesized answers with citations.
        
        **Powered by:**
        - AWS Bedrock (Claude 3.5)
        - OpenSearch Serverless
        - Titan Embeddings
        """)
        
        st.divider()
        st.caption(f"Model: {Config.BEDROCK_MODEL.split('.')[-1]}")
    
    # Initialize session state
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask a question about company documents..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate response
        with st.chat_message("assistant"):
            with st.spinner("Searching documents..."):
                try:
                    rag = get_rag_engine()
                    result = rag.query(prompt)
                    
                    # Display answer
                    st.markdown(result['answer'])
                    
                    # Display sources
                    with st.expander("📎 View Sources"):
                        for i, source in enumerate(result['sources'][:5], 1):
                            st.markdown(f"**{i}. {source['source_file']}** (Page {source['page_number']})")
                            st.caption(source['text'][:200] + "...")
                            st.divider()
                    
                    # Save to history
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": result['answer']
                    })
                
                except Exception as e:
                    error_msg = f"❌ Error: {str(e)}\n\nPlease check your AWS configuration."
                    st.error(error_msg)
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": error_msg
                    })

if __name__ == "__main__":
    main()

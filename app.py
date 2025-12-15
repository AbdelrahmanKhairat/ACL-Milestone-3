"""
Airline Company Flight Insights Assistant - Streamlit UI
=========================================================
Graph-RAG powered assistant for airline insights and analysis.
Step 4: UI Implementation for Milestone 3
"""

import streamlit as st
import sys
import os
from typing import Dict, Any

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from llm_layer.graph_rag_pipeline import GraphRAGPipeline, load_config

# Page configuration
st.set_page_config(
    page_title="Airline Insights Assistant",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .success-box {
        background-color: #d4edda;
        border-left: 4px solid #28a745;
        padding: 1rem;
        margin: 1rem 0;
    }
    .info-box {
        background-color: #e3f2fd;
        border-left: 4px solid #1976d2;
        padding: 1rem;
        margin: 1rem 0;
        color: #000000;
        font-size: 1rem;
        line-height: 1.6;
    }
    .context-box {
        background-color: #2d2d2d;
        border: 1px solid #444;
        padding: 1rem;
        border-radius: 0.25rem;
        font-family: monospace;
        font-size: 0.9rem;
        max-height: 400px;
        overflow-y: auto;
        color: #f0f0f0;
        white-space: pre-wrap;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def initialize_pipeline(model_name: str, embedding_model: str, hf_token: str):
    """Initialize the Graph-RAG pipeline with caching."""
    cfg = load_config()

    pipeline = GraphRAGPipeline(
        neo4j_uri=cfg["URI"],
        neo4j_username=cfg["USERNAME"],
        neo4j_password=cfg["PASSWORD"],
        hf_token=hf_token,
        default_model=model_name,
        embedding_model=embedding_model
    )
    return pipeline


def format_context(context: str, max_length: int = 2000) -> str:
    """Format context for display."""
    if len(context) > max_length:
        return context[:max_length] + f"\n\n... [Truncated - Total: {len(context)} characters]"
    return context


def display_retrieval_stats(result: Dict[str, Any]):
    """Display retrieval statistics."""
    col1, col2, col3 = st.columns(3)

    cypher_count = result.get("cypher_results", {}).get("count", 0) if result.get("cypher_results") else 0
    embed_count = result.get("embedding_results", {}).get("count", 0) if result.get("embedding_results") else 0

    with col1:
        st.metric(
            label="Cypher Results",
            value=cypher_count,
            help="Number of journeys retrieved from Cypher query"
        )

    with col2:
        st.metric(
            label="Embedding Results",
            value=embed_count,
            help="Number of journeys from semantic similarity search"
        )

    with col3:
        response_time = result.get("llm_response", {}).get("response_time", 0)
        st.metric(
            label="Response Time",
            value=f"{response_time:.2f}s",
            help="LLM generation time"
        )


def main():
    # Header
    st.markdown('<div class="main-header">✈️ Airline Company Flight Insights Assistant</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Graph-RAG powered insights from your Knowledge Graph</div>', unsafe_allow_html=True)

    # Sidebar - Configuration
    with st.sidebar:
        st.header("⚙️ Configuration")

        # HuggingFace Token
        hf_token = st.text_input(
            "HuggingFace Token",
            type="password",
            value="hf_token",
            help="Your HuggingFace API token for LLM access"
        )

        st.divider()

        # Model Selection
        st.subheader("🤖 Models")
        model_choice = st.selectbox(
            "LLM Model",
            options=["qwen", "openai", "llama"],
            index=0,
            help="Choose which LLM to use for generating answers"
        )

        embedding_choice = st.selectbox(
            "Embedding Model",
            options=["mpnet", "minilm"],
            index=0,
            help="Choose embedding model for semantic search"
        )

        model_names = {
            "qwen": "Qwen/Qwen2.5-7B-Instruct",
            "openai": "gpt-oss-120b (via Groq)",
            "llama": "Llama-3.1-8B-Instruct"
        }
        st.caption(f"Using LLM: {model_names[model_choice]}")

        st.divider()

        # Retrieval Method Selection
        st.subheader("🔍 Retrieval Method")

        use_cypher = st.checkbox("Cypher Queries (Baseline)", value=True, help="Use structured Cypher queries")
        use_embeddings = st.checkbox("Semantic Embeddings", value=True, help="Use vector similarity search")

        if not use_cypher and not use_embeddings:
            st.warning("⚠️ At least one retrieval method must be enabled!")

        st.divider()

        # Display Options
        st.subheader("👁️ Display Options")
        show_metrics = st.checkbox("Show Metrics", value=True)
        show_prompt = st.checkbox("Show LLM Prompt", value=False)
        show_raw = st.checkbox("Show Raw Intermediate Results", value=False, help="Show raw JSON from Cypher and Embeddings")
        show_context = st.checkbox("Show Combined Context", value=True)
        show_cypher = st.checkbox("Show Cypher Query", value=False)
        

        st.divider()

        # About
        with st.expander("ℹ️ About"):
            st.markdown("""
            **Airline Company Flight Insights Assistant**

            This Graph-RAG system helps airline companies gain insights from their flight data by:
            - Analyzing flight delays and performance
            - Identifying passenger satisfaction issues
            - Finding patterns in routes and operations

            **Tech Stack:**
            - Neo4j Knowledge Graph
            - Vector Embeddings (MPNet)
            - LLM (Qwen/OpenAI/Llama)
            - Streamlit UI
            """)

    # Main content
    if not hf_token or hf_token == "your_token_here":
        st.error("⚠️ Please enter a valid HuggingFace token in the sidebar to continue.")
        st.stop()

    # Initialize pipeline
    try:
        # Re-initialize if embedding model changes (using key to force re-run if needed, but cache takes care of args)
        with st.spinner("Initializing Graph-RAG pipeline..."):
            pipeline = initialize_pipeline(model_choice, embedding_choice, hf_token)
        st.success("✅ Pipeline initialized successfully!")
    except Exception as e:
        st.error(f"❌ Failed to initialize pipeline: {str(e)}")
        st.stop()

    # Question Input
    st.header("💬 Ask Your Question")

    # Example questions
    example_questions = [
        "Which flights have the longest delays?",
        "Show me flights with delays from ORD",
        "Which flights have poor passenger experience?",
        "Find economy class flights",
        "Show me flights with bad food quality",
        "Recommend a good flight route",
        "What are the best business class flights?",
        "What is the average delay for Boomer passengers?",
        "How many journeys were taken by Gen Z?",
    ]

    selected_example = st.selectbox(
        "Or select an example:",
        options=["(Custom question)"] + example_questions,
        index=0
    )

    if selected_example != "(Custom question)":
        question = selected_example
        question_input = st.text_area("Your Question:", value=question, height=100, key="question_area")
    else:
        question_input = st.text_area(
            "Your Question:",
            placeholder="e.g., Which flights have the longest delays?",
            height=100,
            key="question_area"
        )

    # Submit button
    col1, col2, col3 = st.columns([1, 1, 3])
    with col1:
        submit_button = st.button("🚀 Get Insights", type="primary", use_container_width=True)
    with col2:
        clear_button = st.button("🗑️ Clear", use_container_width=True)

    if clear_button:
        st.rerun()

    # Process question
    if submit_button and question_input:
        with st.spinner("🔍 Analyzing your question..."):
            try:
                # Run pipeline
                result = pipeline.answer_question(
                    question_input,
                    model=model_choice,
                    use_cypher=use_cypher,
                    use_embeddings=use_embeddings
                )

                # Display results
                st.divider()

                # Success/Failure indicator
                if result.get("success"):
                    st.markdown('<div class="success-box"><strong>✅ Query Successful</strong></div>', unsafe_allow_html=True)
                else:
                    st.warning("⚠️ Query completed with warnings. Check the response below.")

                # Retrieval Statistics
                if show_metrics:
                    st.header("📊 Retrieval Statistics")
                    display_retrieval_stats(result)
                    st.divider()

                # Intent and Entities
                if show_metrics:
                    col1, col2 = st.columns(2)

                    with col1:
                        st.subheader("🎯 Detected Intent")
                        intent = result.get("intent", "unknown")
                        st.info(f"**{intent}**")

                    with col2:
                        st.subheader("🏷️ Extracted Entities")
                        entities = result.get("entities", {})
                        found_entities = {k: v for k, v in entities.items() if v is not None}
                        if found_entities:
                            st.json(found_entities)
                        else:
                            st.caption("No specific entities extracted")

                    st.divider()
                
                # Raw Intermediate Results (New Feature)
                if show_raw:
                     st.header("🧾 Raw Intermediate Results")
                     
                     st.subheader("1. Cypher Query Results")
                     if result.get("cypher_results", {}).get("results"):
                         st.json(result["cypher_results"]["results"])
                     else:
                         st.info("No results from Cypher")
                         
                     st.subheader("2. Semantic Embedding Results")
                     if result.get("embedding_results", {}).get("results"):
                         st.json(result["embedding_results"]["results"])
                     else:
                         st.info("No results from Embeddings")
                         
                     st.divider()

                # Retrieved Context
                if show_context:
                    st.header("📦 Retrieved Knowledge Graph Context")

                    context = result.get("combined_context", "No context available")

                    with st.expander("View Full Context", expanded=False):
                        st.markdown(f'<div class="context-box">{format_context(context, max_length=5000)}</div>', unsafe_allow_html=True)

                    st.caption(f"Context length: {len(context)} characters")
                    st.divider()

                # Cypher Query
                if show_cypher and result.get("cypher_results"):
                    st.header("🔎 Executed Cypher Query")
                    cypher_query = result.get("cypher_results", {}).get("query", "N/A")
                    st.code(cypher_query, language="cypher")
                    st.divider()
                    
                # LLM Prompt (New Feature)
                if show_prompt:
                    st.header("📝 LLM Prompt")
                    prompt = result.get("prompt", "No prompt available")
                    with st.expander("View Full Prompt", expanded=False):
                        st.code(prompt, language="text")
                    st.divider()

                # LLM Answer
                st.header("💡 Assistant Answer")
                answer = result.get("answer", "No answer generated")

                st.markdown(f'<div class="info-box">{answer}</div>', unsafe_allow_html=True)

                # Additional metrics
                if show_metrics:
                    st.divider()
                    st.subheader("📈 Additional Metrics")

                    col1, col2 = st.columns(2)
                    with col1:
                        prompt_length = len(result.get("prompt", ""))
                        st.metric("Prompt Length", f"{prompt_length} chars")

                    with col2:
                        response_length = len(answer)
                        st.metric("Response Length", f"{response_length} chars")

            except Exception as e:
                st.error(f"❌ Error processing question: {str(e)}")
                st.exception(e)

    elif submit_button:
        st.warning("⚠️ Please enter a question first!")

    # Footer
    st.divider()
    st.caption("🎓 Milestone 3 - Graph-RAG Travel Assistant | GUC CSEN 903")


if __name__ == "__main__":
    main()

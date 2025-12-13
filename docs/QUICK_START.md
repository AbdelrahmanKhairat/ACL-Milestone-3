# Quick Start Guide - Milestone 3

## 🚀 Launch the Streamlit UI

```bash
cd c:\Users\LOQ\Desktop\ACL-Milestone-3
venv\Scripts\streamlit.exe run app.py
```

The app will open automatically at: **http://localhost:8501**

---

## 📝 Quick Demo Flow

1. **Keep default settings** in the sidebar (Qwen model, both retrieval methods)
2. **Select an example question:** "Which flights have the longest delays?"
3. **Click "Get Insights"**
4. **Observe the results:**
   - Retrieval statistics (Cypher: 20, Embeddings: 5)
   - Detected intent: `delay_analysis`
   - Retrieved context from Knowledge Graph
   - Final LLM answer with specific flight numbers and delay times

---

## 🎯 What to Demo in Presentation

### 1. Show the UI (2 minutes)
- Live demo of asking a question
- Show KG context retrieval
- Display LLM answer

### 2. Model Comparison (1 minute)
- Switch to OpenAI model in sidebar
- Run same question
- Show different response style

### 3. Retrieval Methods (1 minute)
- Toggle retrieval methods (Cypher only vs both)
- Show how it affects results

### 4. Metrics Display (1 minute)
- Point out response time
- Show retrieval counts
- Highlight transparency features

---

## 📊 Key Files for Presentation

### Test Results
- [outputs/model_comparison_20251209_145537.txt](outputs/model_comparison_20251209_145537.txt)
  - **Use this for:** Quantitative comparison tables

### Code Architecture
- [llm_layer/graph_rag_pipeline.py](llm_layer/graph_rag_pipeline.py)
  - **Use this for:** Explaining the 4-step pipeline

### UI Code
- [app.py](app.py)
  - **Use this for:** Showing UI implementation

---

## ✅ Milestone 3 Checklist

- [x] **Step 1:** Input Preprocessing (Intent + Entities + Embeddings)
- [x] **Step 2:** Graph Retrieval (Cypher + Semantic Similarity)
- [x] **Step 3:** LLM Layer (3 models + Comparison)
- [x] **Step 4:** Streamlit UI (All required + optional features)

---

## 🎓 Assignment Compliance Summary

| Requirement | Status | Evidence |
|-------------|--------|----------|
| Intent Classification | ✅ | [preprocessing/intent-classifier.py](preprocessing/intent-classifier.py) |
| Entity Extraction | ✅ | [preprocessing/entity_extractor.py](preprocessing/entity_extractor.py) |
| 10+ Cypher Queries | ✅ | [retrieval/query_templates.py](retrieval/query_templates.py) - 10+ templates |
| Embeddings (2 models) | ✅ | MiniLM + MPNet tested |
| 3 LLM Models | ✅ | Qwen, OpenAI, Llama |
| Quantitative Metrics | ✅ | [outputs/model_comparison_20251209_145537.txt](outputs/model_comparison_20251209_145537.txt) |
| Streamlit UI | ✅ | [app.py](app.py) |
| View KG Context | ✅ | Full context display in UI |
| View LLM Answer | ✅ | Formatted answer display |

---

## 🏆 Key Achievements

### Technical Excellence
- **Context Optimization:** Reduced from 514KB to ~5KB (99% reduction)
- **Hybrid Retrieval:** Combines structured + semantic search
- **Multi-Model Support:** Easy switching between 3 LLMs
- **Production-Ready UI:** Professional Streamlit application

### Testing Coverage
- **15 diverse questions** across all intent types
- **3 models tested** with quantitative comparison
- **OpenAI ranked #1** (66.7% success, 1.82s avg time)

---

## 💡 Tips for Presentation

1. **Start with UI demo** - Visual impact
2. **Explain the pipeline** - Show understanding
3. **Highlight innovations** - Context optimization, hybrid retrieval
4. **Show metrics** - Quantitative evidence
5. **Acknowledge limitations** - HF credit limits, entity recognition gaps

---

## 🔧 Troubleshooting

### If Streamlit doesn't start:
```bash
venv\Scripts\pip.exe install streamlit
```

### If Neo4j connection fails:
- Ensure Neo4j is running
- Check credentials in `config.txt`

### If HF API errors (402):
- You've hit the free tier monthly limit
- Wait for next month or use different account

---

## 📦 What to Submit

1. **GitHub Repository**
   - Branch: `Milestone3`
   - All code committed

2. **Presentation Slides**
   - Architecture diagrams
   - Test results
   - UI screenshots
   - Model comparison

3. **Documentation** (already done!)
   - [MILESTONE_3_SUMMARY.md](MILESTONE_3_SUMMARY.md)
   - [README_UI.md](README_UI.md)
   - This quick start guide

---

**You're all set for the presentation!** 🎉

**Demo Command:**
```bash
venv\Scripts\streamlit.exe run app.py
```

Good luck! 🍀

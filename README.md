# VidExplainAgent

An AI-powered system that makes STEM video content accessible to blind and low vision (BLV) learners through automated visual description generation and interactive question-answering.

## 🎯 Overview

VidExplainAgent uses a multimodal RAG (Retrieval-Augmented Generation) pipeline to:

1. Extract and describe visual elements from educational videos using Vision-Language Models
2. Index content in a vector database for semantic search
3. Answer natural language questions about video content
4. Generate accessible audio descriptions

## 📊 Evaluation Results

Comprehensive two-tier evaluation on Wave-Particle Duality video (Physics, 3:32):

### Component-Level (VLM)

- **BERTScore F1: 0.588** - Strong semantic understanding
- **ROUGE-L F1: 0.248** - Moderate phrase similarity
- **BLEU-4: 0.045** - Lexical variation (expected for generative models)

### RAG System (End-to-End)

- **Context Relevance: 100%** ⭐⭐⭐ Perfect retrieval
- **Answer Faithfulness: 90%** - Minimal hallucination
- **Answer Relevancy: 85%** - Addresses questions well
- **Answer Correctness: 75%** - Good factual accuracy
- **Overall Pass Rate: 87.5%** - Excellent performance

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    VidExplainAgent                       │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Frontend (Next.js/React)                               │
│    ├─ Video Upload & YouTube URL Input                  │
│    ├─ Interactive Chat Interface                        │
│    ├─ Voice Input (Web Speech API)                      │
│    └─ Audio Playback (TTS)                              │
│                                                          │
│  Backend (FastAPI)                                       │
│    ├─ Ingestion Pipeline                                │
│    │   ├─ Gemini 2.5 Flash (Multimodal VLM)            │
│    │   ├─ Video Processing                              │
│    │   └─ ChromaDB Indexing                             │
│    │                                                     │
│    └─ Query Pipeline                                     │
│        ├─ Semantic Search (ChromaDB)                    │
│        ├─ RAG with Gemini                               │
│        └─ TTS Generation                                │
│                                                          │
│  Evaluation Framework                                    │
│    ├─ Component: BLEU, ROUGE, BERTScore                │
│    ├─ RAG: RAGAS (Context, Faithfulness, Relevancy)    │
│    └─ Human Evaluation Templates                        │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.13+
- Node.js 18+
- Google GenAI API Key
- OpenAI API Key (for evaluation only)

### Backend Setup

```bash
cd backend

# Install dependencies (using uv)
uv pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY

# Run server
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

Access the app at `http://localhost:3000`

### Evaluation Framework

```bash
cd evaluation

# Install evaluation dependencies
pip install -r requirements.txt

# Set OpenAI API key
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# Run complete evaluation
python scripts/run_ragas_simple.py \
  --qa-pairs data/ground_truth/qa_pairs.json \
  --system-responses results/system_responses.json \
  --output results/ragas_scores.json
```

## 📁 Project Structure

```
VidExplainAgent/
├── backend/
│   ├── src/
│   │   ├── main.py                    # FastAPI application
│   │   ├── ingestion_pipeline.py     # Video processing & indexing
│   │   ├── explanation_synthesis.py  # RAG & TTS generation
│   │   └── config.py                 # Configuration
│   ├── static/audio/                  # Generated TTS audio
│   ├── db/                            # ChromaDB vector store
│   └── history/                       # Processing logs
│
├── frontend/
│   ├── app/
│   │   ├── page.tsx                  # Main UI component
│   │   ├── layout.tsx                # App layout
│   │   └── globals.css               # Styles
│   └── public/                       # Static assets
│
├── evaluation/
│   ├── data/
│   │   ├── ground_truth/             # Human annotations
│   │   └── test_video/               # Test video info
│   ├── scripts/
│   │   ├── run_ragas_simple.py       # RAGAS evaluation
│   │   ├── run_component_eval.py     # BLEU/ROUGE/BERTScore
│   │   └── generate_system_outputs.py # Output generation
│   ├── src/
│   │   ├── component_eval.py         # Component metrics
│   │   ├── rag_eval.py               # RAG metrics
│   │   ├── human_eval.py             # Human evaluation
│   │   └── visualization.py          # Result plotting
│   ├── results/                      # Evaluation outputs
│   └── templates/                    # Report templates
│
├── pyproject.toml                     # Python dependencies
└── docker-compose.yml                 # Docker configuration
```

## 🔬 Key Features

### 1. Multimodal Video Processing

- Gemini 2.5 Flash for visual understanding
- Temporal segmentation of video content
- Rich metadata extraction (concepts, difficulty, speakers)

### 2. Intelligent RAG Pipeline

- ChromaDB vector database with semantic search
- Context-aware answer generation
- Exponential backoff for API reliability

### 3. Accessibility-First Design

- Voice input for hands-free interaction
- TTS audio responses
- Screen reader compatible interface
- Progressive disclosure of complex information

### 4. Comprehensive Evaluation

- **Component-level**: BLEU, ROUGE, BERTScore
- **End-to-end**: RAGAS framework (Context Relevance, Faithfulness, Relevancy, Correctness)
- **Human evaluation**: Likert scale templates ready

## 📊 Evaluation Details

Full evaluation report: `evaluation/results/COMPLETE_EVALUATION_REPORT.md`

**Test Video**: Wave-Particle Duality (Perimeter Institute for Theoretical Physics)

- Duration: 3:32
- Subject: Quantum Physics
- Complexity: Moderate (animations, equations, concepts)

**Datasets**:

- 23 human-annotated visual descriptions
- 20 Q&A pairs with ground truth
- Expert-verified annotations

**Key Finding**: Perfect retrieval (100%) + high faithfulness (90%) + strong semantic understanding (0.588) = reliable, trustworthy system for accessible STEM education.

## 🎓 Academic References

- **BLEU**: Papineni et al. (2002) - N-gram overlap metric
- **ROUGE**: Lin (2004) - Sequence similarity
- **BERTScore**: Zhang et al. (2019) - Semantic similarity with BERT
- **RAGAS**: Es et al. (2023) - RAG-specific evaluation framework

## 🛠️ Technologies

**Backend**:

- FastAPI (Python web framework)
- Google Gemini 2.5 Flash (Vision-Language Model)
- ChromaDB (Vector database)
- Uvicorn (ASGI server)

**Frontend**:

- Next.js 14 (React framework)
- TypeScript
- Tailwind CSS
- Web Speech API (voice input)

**Evaluation**:

- RAGAS (RAG evaluation)
- NLTK, rouge-score, bert-score (text metrics)
- Matplotlib, Seaborn (visualization)

## 📝 License

All rights reserved.

## 👥 Contributors

Syed Ali Haider

## 📧 Contact

For questions or collaboration: syed.ali.haider.gr@dartmouth.edu

---

**Developed for**: Video Understanding Course
**Date**: November 2025  
**Status**: ✅ Production-ready with comprehensive evaluation

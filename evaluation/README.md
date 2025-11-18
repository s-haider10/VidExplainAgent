# VidExplainAgent RAG System Evaluation Framework

Comprehensive two-tiered evaluation framework for assessing the VidExplainAgent RAG system using component-level and end-to-end metrics.

## Overview

This framework implements rigorous evaluation methodology for measuring the quality of:
1. **Component-Level (VLM)**: Visual description generation using BLEU, ROUGE, and BERTScore
2. **End-to-End (RAG)**: Complete question-answering pipeline using RAGAS metrics
3. **Human Evaluation**: User perception of system quality using 5-point Likert scales

## Installation

```bash
cd evaluation
pip install -r requirements.txt
```

### Dependencies

- **ragas**: RAG-specific evaluation metrics
- **nltk**: BLEU score computation
- **rouge-score**: ROUGE metrics
- **bert-score**: Semantic similarity with BERT embeddings
- **sentence-transformers**: Embedding models
- **pandas, numpy, matplotlib**: Data processing and visualization

## Quick Start

### 1. Prepare Ground Truth Data

Create or update the following files in `data/ground_truth/`:

- `manual_annotations.json`: Expert-annotated visual descriptions
- `qa_pairs.json`: Ground truth question-answer pairs
- `video_metadata.json`: Video information

See templates in `data/ground_truth/` for the required format.

### 2. Generate System Outputs

Process your test video through VidExplainAgent and collect:
- Generated visual descriptions (JSON format)
- System responses to Q&A pairs (JSON format)

### 3. Run Evaluations

**Component-Level Evaluation:**
```bash
python scripts/run_component_eval.py \
  --ground-truth data/ground_truth/manual_annotations.json \
  --generated path/to/system_output.json \
  --output results/component_scores.json
```

**RAG System Evaluation:**
```bash
export OPENAI_API_KEY=your_key_here  # Required for RAGAS

python scripts/run_rag_eval.py \
  --qa-pairs data/ground_truth/qa_pairs.json \
  --system-responses path/to/system_responses.json \
  --output results/rag_scores.json
```

**Complete Evaluation Suite:**
```bash
python scripts/run_all_evaluations.py \
  --ground-truth data/ground_truth/manual_annotations.json \
  --generated path/to/system_output.json \
  --qa-pairs data/ground_truth/qa_pairs.json \
  --system-responses path/to/system_responses.json \
  --output-dir results/
```

### 4. Human Evaluation (Optional)

**Generate evaluation forms:**
```python
from src.human_eval import HumanEvaluationFramework

framework = HumanEvaluationFramework()
framework.generate_evaluation_form(
    qa_pairs_file="data/ground_truth/qa_pairs.json",
    system_responses_file="path/to/system_responses.json",
    output_file="results/human_eval_form.csv"
)
```

**Analyze responses:**
```python
results = framework.analyze_responses("results/completed_evaluations.csv")
```

### 5. Generate Visualizations

```python
from src.visualization import generate_all_visualizations

generate_all_visualizations(
    component_file="results/component_scores.json",
    rag_file="results/rag_scores.json",
    human_file="results/human_eval_results.json",  # Optional
    output_dir="results/figures"
)
```

## Evaluation Metrics

### Component-Level (VLM) Metrics

Evaluates quality of generated visual descriptions:

| Metric | Description | Target | Range |
|--------|-------------|--------|-------|
| **BLEU-1 to BLEU-4** | N-gram overlap with ground truth | > 0.3 | 0-1 |
| **ROUGE-L** | Longest common subsequence | > 0.4 | 0-1 |
| **BERTScore** | Semantic similarity using BERT | > 0.85 | 0-1 |

### End-to-End (RAG) Metrics

Evaluates complete question-answering pipeline using RAGAS:

| Metric | Description | Target | Range |
|--------|-------------|--------|-------|
| **Context Relevance** | Relevance of retrieved chunks | > 0.8 | 0-1 |
| **Answer Faithfulness** | Grounding in retrieved context | > 0.9 | 0-1 |
| **Context Precision** | Proportion of relevant chunks | > 0.7 | 0-1 |
| **Context Recall** | Coverage of ground truth | > 0.7 | 0-1 |
| **Answer Relevancy** | How well answer addresses question | > 0.8 | 0-1 |

### Human Evaluation Dimensions

5-point Likert scale (1 = Strongly Disagree, 5 = Strongly Agree):

- **Helpfulness**: Answer helps understand video content (Target: > 4.0)
- **Clarity**: Explanation is easy to understand (Target: > 4.0)
- **Completeness**: Answer fully addresses the question (Target: > 3.5)
- **Accessibility**: BLV users can follow the explanation (Target: > 4.0)

## Data Format Specifications

### Ground Truth Annotations

```json
{
  "video_url": "https://youtube.com/watch?v=...",
  "annotations": [
    {
      "timestamp_start": "00:01:15",
      "timestamp_end": "00:01:25",
      "ground_truth_visual_description": "Detailed expert annotation...",
      "ground_truth_transcript": "Exact spoken words...",
      "key_concepts": ["Concept1", "Concept2"],
      "difficulty": "beginner"
    }
  ]
}
```

### Q&A Pairs

```json
{
  "video_url": "https://youtube.com/watch?v=...",
  "qa_pairs": [
    {
      "id": "q1",
      "question": "What is shown at 1:15?",
      "ground_truth_answer": "Expert-written answer...",
      "ground_truth_context": ["Relevant context chunks..."],
      "difficulty": "easy"
    }
  ]
}
```

### System Responses

```json
{
  "responses": [
    {
      "question_id": "q1",
      "question": "What is shown at 1:15?",
      "answer": "System-generated answer...",
      "retrieved_contexts": ["Context chunk 1", "Context chunk 2"]
    }
  ]
}
```

## Output Files

After running evaluations, the following files are generated in `results/`:

- `component_scores.json`: Component-level metrics
- `rag_scores.json`: RAG system metrics
- `human_eval_results.json`: Human evaluation statistics
- `final_report.md`: Comprehensive results report
- `figures/`: Visualizations and plots
- `comparison_table.csv`: All metrics in tabular format

## Methodology

### Component-Level Evaluation

1. Load ground truth annotations and system-generated descriptions
2. Match descriptions by timestamp
3. Calculate BLEU, ROUGE, and BERTScore for each pair
4. Aggregate statistics (mean, median, std, min, max)
5. Generate visualizations and detailed report

### RAG System Evaluation

1. Prepare dataset with questions, answers, contexts, and ground truth
2. Run RAGAS evaluation using OpenAI models
3. Compute context relevance, answer faithfulness, and other metrics
4. Analyze per-question performance
5. Generate comprehensive report with statistical analysis

### Human Evaluation

1. Generate randomized evaluation forms
2. Distribute to evaluators with clear instructions
3. Collect responses via CSV
4. Calculate Likert scale statistics
5. Compute inter-rater reliability (Krippendorff's alpha)
6. Perform qualitative analysis of comments

## Academic Rigor

This framework ensures academic rigor through:

- **Statistical Significance**: Confidence intervals and significance testing
- **Reproducibility**: Fixed random seeds, version pinning
- **Reliability**: Inter-annotator agreement metrics
- **Transparency**: Detailed logging and intermediate results
- **Validation**: Multiple complementary metrics

## Citation

If you use this evaluation framework in your research, please cite:

```bibtex
@software{videxplainagent_eval,
  title={VidExplainAgent Evaluation Framework},
  author={Your Name},
  year={2025},
  url={https://github.com/your-repo}
}
```

## References

- **RAGAS**: [es2025ragasautomatedevaluationretrieval]
- **BLEU**: Papineni et al. (2002)
- **ROUGE**: Lin (2004)
- **BERTScore**: Zhang et al. (2019)

## License

[Your License]

## Contact

For questions or issues, please contact: [Your Contact Info]

---

**Last Updated**: January 2025


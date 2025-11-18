# RAGAS Framework Testing Guide

This guide explains how to test the RAGAS framework for evaluating your RAG system.

## Overview

RAGAS (Retrieval-Augmented Generation Assessment) is a framework for evaluating RAG systems. We have two scripts available:

1. **`scripts/test_ragas.py`** - Uses standard RAGAS metrics (ContextRelevance, AnswerRelevancy, Faithfulness)
2. **`scripts/run_ragas_simple.py`** - Uses custom DiscreteMetric approach with pass/fail scoring

## Prerequisites

1. **Install dependencies** (if not already installed):
   ```bash
   cd evaluation
   pip install -r requirements.txt
   ```

2. **Set up OpenAI API Key**:
   - RAGAS requires OpenAI API access for LLM-based evaluation
   - Create or update `.env` file in the `evaluation/` directory:
     ```
     OPENAI_API_KEY=your-api-key-here
     ```

## Running the Tests

### Option 1: Simple RAGAS Test (Recommended)

This uses the simplified approach with custom metrics:

```bash
cd evaluation
source ../.venv/bin/activate  # or activate your virtual environment
python scripts/run_ragas_simple.py \
  --qa-pairs data/ground_truth/qa_pairs.json \
  --system-responses results/system_responses_test.json \
  --output results/ragas_simple_test.json
```

### Option 2: Standard RAGAS Test

This uses the standard RAGAS evaluation framework:

```bash
cd evaluation
source ../.venv/bin/activate
python scripts/test_ragas.py \
  --qa-pairs data/ground_truth/qa_pairs.json \
  --system-responses results/system_responses_test.json \
  --output results/ragas_test_results.json
```

## Understanding the Results

### Metrics Evaluated

1. **Answer Relevancy**: How well the answer addresses the question
2. **Answer Correctness**: Factual accuracy compared to ground truth
3. **Answer Faithfulness**: Whether the answer is grounded in the retrieved context (not hallucinated)
4. **Context Relevance**: How relevant the retrieved context is to the question

### Output Format

The scripts generate:
- **JSON file**: Detailed results with per-question scores and summary statistics
- **CSV file** (test_ragas.py only): Tabular format for easy analysis

### Example Output

```json
{
  "num_samples": 5,
  "metrics_summary": {
    "answer_relevancy": {
      "pass_count": 4,
      "fail_count": 1,
      "total_evaluated": 5,
      "pass_rate": 0.8,
      "score": 0.8
    },
    ...
  },
  "detailed_results": [...]
}
```

## Troubleshooting

### API Key Issues

If you see errors like "Incorrect API key provided":
1. Check that your `.env` file contains a valid `OPENAI_API_KEY`
2. Verify the API key is active at https://platform.openai.com/account/api-keys
3. Make sure the `.env` file is in the `evaluation/` directory

### Missing Contexts

If you see "no_context" in results:
- The system responses should include `retrieved_contexts` field
- If missing, the script will try to use `ground_truth_context` from Q&A pairs
- For best results, ensure your system responses include the retrieved contexts

### Version Compatibility

If you encounter errors about `agenerate` or `InstructorLLM`:
- Make sure you're using RAGAS 0.3.9 or compatible version
- The scripts have been updated to use the new `llm_factory` API
- If issues persist, try updating RAGAS: `pip install --upgrade ragas`

## Data Format Requirements

### Q&A Pairs (`qa_pairs.json`)
```json
{
  "qa_pairs": [
    {
      "id": "q1",
      "question": "Your question here",
      "ground_truth_answer": "Expected answer",
      "ground_truth_context": ["Relevant context chunks"]
    }
  ]
}
```

### System Responses (`system_responses.json`)
```json
{
  "responses": [
    {
      "question_id": "q1",
      "question": "Your question here",
      "answer": "System-generated answer",
      "retrieved_contexts": ["Context chunk 1", "Context chunk 2"]
    }
  ]
}
```

## Next Steps

1. **Review Results**: Check the detailed results to identify areas for improvement
2. **Iterate**: Make improvements to your RAG system based on the evaluation
3. **Re-evaluate**: Run the evaluation again to measure improvements
4. **Compare**: Track metrics over time to monitor system performance

## Additional Resources

- [RAGAS Documentation](https://docs.ragas.io/)
- [RAGAS GitHub](https://github.com/explodinggradients/ragas)
- Evaluation framework README: `evaluation/README.md`


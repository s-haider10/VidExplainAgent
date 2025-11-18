"""
End-to-End RAG System Evaluation using RAGAS

Evaluates the complete RAG pipeline using:
- Context Relevance: How relevant are retrieved chunks to the query
- Answer Faithfulness: Is the answer grounded in the context
- Context Precision: Proportion of relevant chunks
- Context Recall: Coverage of ground truth context
- Answer Relevancy: How well the answer addresses the question
"""

import logging
from typing import Dict, List, Any
import os
from tqdm import tqdm

from ragas import evaluate
from ragas.metrics import (
    ContextRelevance,
    Faithfulness,
    AnswerRelevancy,
    ContextPrecision,
    ContextRecall
)
from datasets import Dataset

from utils import load_json, save_json, calculate_statistics

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RAGEvaluator:
    """Evaluates end-to-end RAG system performance using RAGAS."""
    
    def __init__(self, openai_api_key: str = None):
        """
        Initialize RAG evaluator.
        
        Args:
            openai_api_key: OpenAI API key for RAGAS (uses env var if None)
        """
        if openai_api_key:
            os.environ["OPENAI_API_KEY"] = openai_api_key
        elif "OPENAI_API_KEY" not in os.environ:
            logger.warning("OPENAI_API_KEY not set. RAGAS requires OpenAI API access.")
        
        self.metrics = [
            ContextRelevance(),
            AnswerRelevancy(),
            Faithfulness(),
            ContextPrecision(),
            ContextRecall()
        ]
    
    def prepare_evaluation_dataset(
        self,
        qa_pairs_file: str,
        system_responses_file: str
    ) -> Dataset:
        """
        Prepare dataset in RAGAS format.
        
        Args:
            qa_pairs_file: Ground truth Q&A pairs JSON
            system_responses_file: System-generated responses JSON
            
        Returns:
            HuggingFace Dataset for RAGAS evaluation
        """
        logger.info("Preparing evaluation dataset...")
        
        qa_pairs = load_json(qa_pairs_file)
        system_responses = load_json(system_responses_file)
        
        # Build dataset
        data = {
            'question': [],
            'answer': [],
            'contexts': [],
            'ground_truth': [],
            'ground_truth_contexts': []
        }
        
        for qa in qa_pairs['qa_pairs']:
            question_id = qa.get('id', qa['question'])
            
            # Find matching system response
            system_response = next(
                (r for r in system_responses['responses'] 
                 if r.get('question_id') == question_id or r['question'] == qa['question']),
                None
            )
            
            if system_response:
                data['question'].append(qa['question'])
                data['answer'].append(system_response['answer'])
                data['contexts'].append(system_response.get('retrieved_contexts', []))
                data['ground_truth'].append(qa['ground_truth_answer'])
                data['ground_truth_contexts'].append(qa.get('ground_truth_context', []))
            else:
                logger.warning(f"No system response found for question: {qa['question']}")
        
        logger.info(f"Prepared {len(data['question'])} evaluation samples")
        return Dataset.from_dict(data)
    
    def evaluate_rag_system(
        self,
        qa_pairs_file: str,
        system_responses_file: str
    ) -> Dict[str, Any]:
        """
        Run complete RAGAS evaluation.
        
        Args:
            qa_pairs_file: Ground truth Q&A pairs
            system_responses_file: System responses
            
        Returns:
            Evaluation results with all RAGAS metrics
        """
        logger.info("Starting RAGAS evaluation...")
        
        # Prepare dataset
        dataset = self.prepare_evaluation_dataset(qa_pairs_file, system_responses_file)
        
        if len(dataset) == 0:
            raise ValueError("No matching Q&A pairs found for evaluation")
        
        # Run RAGAS evaluation
        logger.info("Computing RAGAS metrics (this may take a while)...")
        results = evaluate(
            dataset,
            metrics=self.metrics,
        )
        
        # Process results
        scores_df = results.to_pandas()
        
        # Calculate statistics for each metric
        metric_stats = {}
        for metric_name in scores_df.columns:
            if metric_name not in ['question', 'answer', 'contexts', 'ground_truth', 'ground_truth_contexts']:
                scores = scores_df[metric_name].tolist()
                metric_stats[metric_name] = calculate_statistics(scores)
        
        # Create summary
        summary = {
            metric: stats['mean']
            for metric, stats in metric_stats.items()
        }
        
        evaluation_results = {
            'num_samples': len(dataset),
            'metric_statistics': metric_stats,
            'summary': summary,
            'detailed_scores': scores_df.to_dict('records')
        }
        
        # Log results
        logger.info("RAG evaluation complete!")
        for metric, mean_score in summary.items():
            logger.info(f"{metric}: {mean_score:.4f}")
        
        return evaluation_results
    
    def evaluate_context_quality(
        self,
        retrieved_contexts: List[str],
        ground_truth_contexts: List[str],
        query: str
    ) -> Dict[str, float]:
        """
        Evaluate quality of retrieved context chunks.
        
        Args:
            retrieved_contexts: System-retrieved context chunks
            ground_truth_contexts: Ground truth relevant contexts
            query: User query
            
        Returns:
            Dictionary with context quality metrics
        """
        from sentence_transformers import SentenceTransformer, util
        
        model = SentenceTransformer('BAAI/bge-large-en-v1.5')
        
        # Compute embeddings
        query_emb = model.encode(query, convert_to_tensor=True)
        retrieved_embs = model.encode(retrieved_contexts, convert_to_tensor=True)
        gt_embs = model.encode(ground_truth_contexts, convert_to_tensor=True)
        
        # Context Relevance: Average similarity between query and retrieved contexts
        relevance_scores = util.pytorch_cos_sim(query_emb, retrieved_embs)[0]
        avg_relevance = float(relevance_scores.mean())
        
        # Context Coverage: How well retrieved contexts cover ground truth
        coverage_scores = []
        for gt_emb in gt_embs:
            max_sim = max([float(util.pytorch_cos_sim(gt_emb, ret_emb)) 
                          for ret_emb in retrieved_embs])
            coverage_scores.append(max_sim)
        avg_coverage = sum(coverage_scores) / len(coverage_scores) if coverage_scores else 0.0
        
        return {
            'context_relevance': avg_relevance,
            'context_coverage': avg_coverage,
            'num_retrieved': len(retrieved_contexts),
            'num_ground_truth': len(ground_truth_contexts)
        }


def run_rag_evaluation(
    qa_pairs_path: str,
    system_responses_path: str,
    output_path: str,
    openai_api_key: str = None
) -> Dict[str, Any]:
    """
    Run complete RAG evaluation.
    
    Args:
        qa_pairs_path: Path to ground truth Q&A JSON
        system_responses_path: Path to system responses JSON
        output_path: Path to save results
        openai_api_key: OpenAI API key (optional)
        
    Returns:
        Evaluation results dictionary
    """
    evaluator = RAGEvaluator(openai_api_key)
    results = evaluator.evaluate_rag_system(qa_pairs_path, system_responses_path)
    save_json(results, output_path)
    return results


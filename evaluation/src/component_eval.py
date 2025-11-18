"""
Component-Level Evaluation: VLM Visual Description Quality

Evaluates generated visual descriptions against ground truth using:
- BLEU (n-gram overlap)
- ROUGE-L (longest common subsequence)
- BERTScore (semantic similarity)
"""

import logging
from typing import Dict, List, Tuple
import numpy as np
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
from rouge_score import rouge_scorer
from bert_score import score as bert_score
from tqdm import tqdm

from utils import load_json, save_json, calculate_statistics, ensure_nltk_data

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ComponentEvaluator:
    """Evaluates component-level (VLM) performance."""
    
    def __init__(self):
        """Initialize evaluator and ensure dependencies."""
        ensure_nltk_data()
        self.rouge_scorer = rouge_scorer.RougeScorer(['rougeL'], use_stemmer=True)
        self.smoothing = SmoothingFunction().method1
        
    def calculate_bleu(
        self, 
        reference: str, 
        hypothesis: str, 
        max_n: int = 4
    ) -> Dict[str, float]:
        """
        Calculate BLEU scores (BLEU-1 through BLEU-4).
        
        Args:
            reference: Ground truth text
            hypothesis: Generated text
            max_n: Maximum n-gram order (default: 4)
            
        Returns:
            Dictionary with BLEU-1, BLEU-2, BLEU-3, BLEU-4 scores
        """
        reference_tokens = reference.lower().split()
        hypothesis_tokens = hypothesis.lower().split()
        
        scores = {}
        for n in range(1, max_n + 1):
            weights = tuple([1.0 / n] * n + [0.0] * (max_n - n))
            score = sentence_bleu(
                [reference_tokens], 
                hypothesis_tokens, 
                weights=weights,
                smoothing_function=self.smoothing
            )
            scores[f"BLEU-{n}"] = score
            
        return scores
    
    def calculate_rouge(
        self, 
        reference: str, 
        hypothesis: str
    ) -> Dict[str, float]:
        """
        Calculate ROUGE-L scores.
        
        Args:
            reference: Ground truth text
            hypothesis: Generated text
            
        Returns:
            Dictionary with ROUGE-L precision, recall, and F1
        """
        scores = self.rouge_scorer.score(reference, hypothesis)
        rouge_l = scores['rougeL']
        
        return {
            "ROUGE-L-P": rouge_l.precision,
            "ROUGE-L-R": rouge_l.recall,
            "ROUGE-L-F1": rouge_l.fmeasure
        }
    
    def calculate_bertscore(
        self, 
        references: List[str], 
        hypotheses: List[str],
        model_type: str = "bert-base-uncased",
        batch_size: int = 32
    ) -> Dict[str, List[float]]:
        """
        Calculate BERTScore for a list of text pairs.
        
        Args:
            references: List of ground truth texts
            hypotheses: List of generated texts
            model_type: BERT model to use
            batch_size: Batch size for processing
            
        Returns:
            Dictionary with precision, recall, and F1 lists
        """
        logger.info(f"Computing BERTScore for {len(references)} samples...")
        
        P, R, F1 = bert_score(
            hypotheses, 
            references,
            model_type=model_type,
            batch_size=batch_size,
            verbose=False
        )
        
        return {
            "BERTScore-P": P.tolist(),
            "BERTScore-R": R.tolist(),
            "BERTScore-F1": F1.tolist()
        }
    
    def evaluate_descriptions(
        self,
        ground_truth_file: str,
        generated_file: str
    ) -> Dict[str, any]:
        """
        Evaluate all visual descriptions.
        
        Args:
            ground_truth_file: Path to ground truth annotations JSON
            generated_file: Path to generated descriptions JSON
            
        Returns:
            Complete evaluation results with all metrics
        """
        logger.info("Loading ground truth and generated descriptions...")
        ground_truth = load_json(ground_truth_file)
        generated = load_json(generated_file)
        
        # Extract annotations (handle nested structure)
        if 'annotations' in ground_truth and isinstance(ground_truth['annotations'], list):
            if len(ground_truth['annotations']) > 0 and 'annotations' in ground_truth['annotations'][0]:
                # Nested structure
                annotations_list = ground_truth['annotations'][0]['annotations']
            else:
                # Flat structure
                annotations_list = ground_truth['annotations']
        else:
            annotations_list = []
        
        gt_annotations = {
            ann['timestamp_start']: ann['ground_truth_visual_description']
            for ann in annotations_list
        }
        
        gen_annotations = {
            item.get('timestamp_start') or item.get('timestamp_start_str'): item['visual_description']
            for item in generated
        }
        
        # Match timestamps
        matched_pairs = []
        for timestamp in gt_annotations:
            if timestamp in gen_annotations:
                matched_pairs.append({
                    'timestamp': timestamp,
                    'reference': gt_annotations[timestamp],
                    'hypothesis': gen_annotations[timestamp]
                })
            else:
                logger.warning(f"Missing generated description for timestamp {timestamp}")
        
        logger.info(f"Evaluating {len(matched_pairs)} matched descriptions...")
        
        # Calculate metrics for each pair
        all_bleu_scores = {f"BLEU-{i}": [] for i in range(1, 5)}
        all_rouge_scores = {"ROUGE-L-P": [], "ROUGE-L-R": [], "ROUGE-L-F1": []}
        detailed_results = []
        
        for pair in tqdm(matched_pairs, desc="Computing BLEU and ROUGE"):
            # BLEU scores
            bleu = self.calculate_bleu(pair['reference'], pair['hypothesis'])
            for key, value in bleu.items():
                all_bleu_scores[key].append(value)
            
            # ROUGE scores
            rouge = self.calculate_rouge(pair['reference'], pair['hypothesis'])
            for key, value in rouge.items():
                all_rouge_scores[key].append(value)
            
            detailed_results.append({
                'timestamp': pair['timestamp'],
                'scores': {**bleu, **rouge}
            })
        
        # BERTScore (batch processing)
        references = [p['reference'] for p in matched_pairs]
        hypotheses = [p['hypothesis'] for p in matched_pairs]
        bert_scores = self.calculate_bertscore(references, hypotheses)
        
        # Add BERTScore to detailed results
        for i, result in enumerate(detailed_results):
            result['scores'].update({
                'BERTScore-P': bert_scores['BERTScore-P'][i],
                'BERTScore-R': bert_scores['BERTScore-R'][i],
                'BERTScore-F1': bert_scores['BERTScore-F1'][i]
            })
        
        # Calculate aggregated statistics
        aggregated_scores = {}
        
        # BLEU stats
        for metric, scores in all_bleu_scores.items():
            aggregated_scores[metric] = calculate_statistics(scores)
        
        # ROUGE stats
        for metric, scores in all_rouge_scores.items():
            aggregated_scores[metric] = calculate_statistics(scores)
        
        # BERTScore stats
        for metric, scores in bert_scores.items():
            aggregated_scores[metric] = calculate_statistics(scores)
        
        results = {
            'num_samples': len(matched_pairs),
            'aggregated_scores': aggregated_scores,
            'detailed_results': detailed_results,
            'summary': {
                'BLEU-4_mean': aggregated_scores['BLEU-4']['mean'],
                'ROUGE-L-F1_mean': aggregated_scores['ROUGE-L-F1']['mean'],
                'BERTScore-F1_mean': aggregated_scores['BERTScore-F1']['mean']
            }
        }
        
        logger.info("Component evaluation complete!")
        logger.info(f"BLEU-4: {results['summary']['BLEU-4_mean']:.4f}")
        logger.info(f"ROUGE-L F1: {results['summary']['ROUGE-L-F1_mean']:.4f}")
        logger.info(f"BERTScore F1: {results['summary']['BERTScore-F1_mean']:.4f}")
        
        return results


def run_component_evaluation(
    ground_truth_path: str,
    generated_path: str,
    output_path: str
) -> Dict[str, any]:
    """
    Run complete component-level evaluation.
    
    Args:
        ground_truth_path: Path to ground truth JSON
        generated_path: Path to generated descriptions JSON
        output_path: Path to save results
        
    Returns:
        Evaluation results dictionary
    """
    evaluator = ComponentEvaluator()
    results = evaluator.evaluate_descriptions(ground_truth_path, generated_path)
    save_json(results, output_path)
    return results


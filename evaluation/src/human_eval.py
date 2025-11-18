"""
Human Evaluation Framework

Collect and analyze human judgments on:
- Helpfulness (1-5)
- Clarity (1-5)
- Completeness (1-5)
- Accessibility (1-5)
"""

import logging
from typing import Dict, List, Any
import pandas as pd
import numpy as np
from pathlib import Path

from utils import load_json, save_json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HumanEvaluationFramework:
    """Framework for conducting and analyzing human evaluations."""
    
    DIMENSIONS = {
        'helpfulness': "Does the answer help understand the video content?",
        'clarity': "Is the explanation easy to understand?",
        'completeness': "Does the answer fully address the question?",
        'accessibility': "Can a BLV user follow the explanation?"
    }
    
    def __init__(self):
        """Initialize human evaluation framework."""
        pass
    
    def generate_evaluation_form(
        self,
        qa_pairs_file: str,
        system_responses_file: str,
        output_file: str,
        randomize: bool = True
    ) -> None:
        """
        Generate human evaluation forms in CSV format.
        
        Args:
            qa_pairs_file: Ground truth Q&A pairs
            system_responses_file: System generated responses
            output_file: Path to save evaluation form
            randomize: Whether to randomize question order
        """
        qa_pairs = load_json(qa_pairs_file)
        system_responses = load_json(system_responses_file)
        
        # Match questions with responses
        evaluation_items = []
        for qa in qa_pairs['qa_pairs']:
            response = next(
                (r for r in system_responses['responses'] 
                 if r.get('question_id') == qa['id'] or r['question'] == qa['question']),
                None
            )
            
            if response:
                evaluation_items.append({
                    'question_id': qa['id'],
                    'question': qa['question'],
                    'system_answer': response['answer'],
                    'ground_truth': qa['ground_truth_answer'],
                    'helpfulness_score': '',
                    'clarity_score': '',
                    'completeness_score': '',
                    'accessibility_score': '',
                    'comments': ''
                })
        
        # Randomize if requested
        if randomize:
            np.random.shuffle(evaluation_items)
        
        # Create DataFrame and save
        df = pd.DataFrame(evaluation_items)
        df.to_csv(output_file, index=False)
        logger.info(f"Generated evaluation form with {len(evaluation_items)} items: {output_file}")
    
    def analyze_responses(
        self,
        responses_file: str
    ) -> Dict[str, Any]:
        """
        Analyze collected human evaluation responses.
        
        Args:
            responses_file: CSV file with completed evaluations
            
        Returns:
            Analysis results including statistics and reliability
        """
        df = pd.read_csv(responses_file)
        
        # Calculate statistics for each dimension
        dimensions = ['helpfulness_score', 'clarity_score', 'completeness_score', 'accessibility_score']
        results = {
            'num_responses': len(df),
            'dimension_statistics': {},
            'overall_statistics': {},
            'per_question_scores': []
        }
        
        for dim in dimensions:
            scores = pd.to_numeric(df[dim], errors='coerce').dropna()
            results['dimension_statistics'][dim] = {
                'mean': float(scores.mean()),
                'median': float(scores.median()),
                'std': float(scores.std()),
                'min': float(scores.min()),
                'max': float(scores.max()),
                'count': len(scores)
            }
        
        # Overall average across all dimensions
        all_scores = []
        for dim in dimensions:
            all_scores.extend(pd.to_numeric(df[dim], errors='coerce').dropna().tolist())
        
        results['overall_statistics'] = {
            'mean': float(np.mean(all_scores)),
            'median': float(np.median(all_scores)),
            'std': float(np.std(all_scores))
        }
        
        # Per-question analysis
        for idx, row in df.iterrows():
            question_scores = {
                'question_id': row['question_id'],
                'question': row['question'],
                'scores': {}
            }
            for dim in dimensions:
                try:
                    question_scores['scores'][dim] = float(row[dim])
                except:
                    question_scores['scores'][dim] = None
            
            results['per_question_scores'].append(question_scores)
        
        logger.info("Human evaluation analysis complete!")
        for dim, stats in results['dimension_statistics'].items():
            logger.info(f"{dim}: {stats['mean']:.2f} ± {stats['std']:.2f}")
        
        return results
    
    def calculate_inter_rater_reliability(
        self,
        rater_files: List[str],
        method: str = 'krippendorff'
    ) -> Dict[str, float]:
        """
        Calculate inter-rater reliability.
        
        Args:
            rater_files: List of CSV files from different raters
            method: Reliability method ('krippendorff' or 'fleiss_kappa')
            
        Returns:
            Reliability scores for each dimension
        """
        import krippendorff
        
        dimensions = ['helpfulness_score', 'clarity_score', 'completeness_score', 'accessibility_score']
        reliability_scores = {}
        
        for dim in dimensions:
            # Collect ratings from all raters
            all_ratings = []
            for rater_file in rater_files:
                df = pd.read_csv(rater_file)
                ratings = pd.to_numeric(df[dim], errors='coerce').values
                all_ratings.append(ratings)
            
            # Calculate Krippendorff's alpha
            reliability_matrix = np.array(all_ratings)
            alpha = krippendorff.alpha(reliability_matrix, level_of_measurement='ordinal')
            reliability_scores[dim] = float(alpha)
        
        logger.info("Inter-rater reliability:")
        for dim, score in reliability_scores.items():
            logger.info(f"{dim}: α = {score:.3f}")
        
        return reliability_scores
    
    def generate_qualitative_report(
        self,
        responses_file: str,
        output_file: str
    ) -> None:
        """
        Generate qualitative analysis report from comments.
        
        Args:
            responses_file: CSV with evaluations including comments
            output_file: Path to save report
        """
        df = pd.read_csv(responses_file)
        
        report = "# Human Evaluation Qualitative Analysis\n\n"
        report += f"Total Responses: {len(df)}\n\n"
        
        report += "## Comments by Question\n\n"
        
        for idx, row in df.iterrows():
            if pd.notna(row.get('comments')) and str(row['comments']).strip():
                report += f"### {row['question_id']}: {row['question']}\n\n"
                report += f"**Comment:** {row['comments']}\n\n"
                report += f"**Scores:** "
                report += f"Helpfulness={row['helpfulness_score']}, "
                report += f"Clarity={row['clarity_score']}, "
                report += f"Completeness={row['completeness_score']}, "
                report += f"Accessibility={row['accessibility_score']}\n\n"
                report += "---\n\n"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        logger.info(f"Qualitative report saved to {output_file}")


def run_human_evaluation_analysis(
    responses_file: str,
    output_path: str
) -> Dict[str, Any]:
    """
    Run complete human evaluation analysis.
    
    Args:
        responses_file: CSV file with completed evaluations
        output_path: Path to save results JSON
        
    Returns:
        Analysis results
    """
    framework = HumanEvaluationFramework()
    results = framework.analyze_responses(responses_file)
    save_json(results, output_path)
    return results


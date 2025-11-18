"""
Visualization utilities for evaluation results.

Generate plots, charts, and figures for academic presentation.
"""

import logging
from typing import Dict, List, Any
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
from pathlib import Path

from utils import load_json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (10, 6)
plt.rcParams['font.size'] = 12


class EvaluationVisualizer:
    """Generate visualizations for evaluation results."""
    
    def __init__(self, output_dir: str = "../results/figures"):
        """Initialize visualizer with output directory."""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def plot_component_metrics(
        self,
        results_file: str,
        save_path: str = None
    ) -> None:
        """
        Plot component-level metrics (BLEU, ROUGE, BERTScore).
        
        Args:
            results_file: Path to component evaluation results JSON
            save_path: Path to save figure (default: output_dir/component_metrics.png)
        """
        results = load_json(results_file)
        
        # Extract mean scores
        metrics = ['BLEU-1', 'BLEU-2', 'BLEU-3', 'BLEU-4', 'ROUGE-L-F1', 
                  'BERTScore-P', 'BERTScore-R', 'BERTScore-F1']
        means = [results['aggregated_scores'][m]['mean'] for m in metrics]
        stds = [results['aggregated_scores'][m]['std'] for m in metrics]
        
        # Create bar plot
        fig, ax = plt.subplots(figsize=(12, 6))
        x = np.arange(len(metrics))
        bars = ax.bar(x, means, yerr=stds, capsize=5, alpha=0.7, 
                     color=sns.color_palette("husl", len(metrics)))
        
        ax.set_xlabel('Metric', fontsize=14, fontweight='bold')
        ax.set_ylabel('Score', fontsize=14, fontweight='bold')
        ax.set_title('Component-Level Evaluation: Visual Description Quality', 
                    fontsize=16, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(metrics, rotation=45, ha='right')
        ax.set_ylim(0, 1.0)
        ax.grid(axis='y', alpha=0.3)
        
        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{height:.3f}',
                   ha='center', va='bottom', fontsize=10)
        
        plt.tight_layout()
        
        if save_path is None:
            save_path = self.output_dir / "component_metrics.png"
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
        logger.info(f"Component metrics plot saved to {save_path}")
    
    def plot_rag_metrics(
        self,
        results_file: str,
        save_path: str = None
    ) -> None:
        """
        Plot RAG system metrics (RAGAS).
        
        Args:
            results_file: Path to RAG evaluation results JSON
            save_path: Path to save figure
        """
        results = load_json(results_file)
        
        # Extract metrics
        metrics = list(results['summary'].keys())
        scores = list(results['summary'].values())
        
        # Create bar plot
        fig, ax = plt.subplots(figsize=(10, 6))
        colors = sns.color_palette("viridis", len(metrics))
        bars = ax.barh(metrics, scores, color=colors, alpha=0.8)
        
        ax.set_xlabel('Score', fontsize=14, fontweight='bold')
        ax.set_title('End-to-End RAG System Performance (RAGAS)', 
                    fontsize=16, fontweight='bold')
        ax.set_xlim(0, 1.0)
        ax.grid(axis='x', alpha=0.3)
        
        # Add value labels
        for bar in bars:
            width = bar.get_width()
            ax.text(width, bar.get_y() + bar.get_height()/2.,
                   f'{width:.3f}',
                   ha='left', va='center', fontsize=11, fontweight='bold')
        
        plt.tight_layout()
        
        if save_path is None:
            save_path = self.output_dir / "rag_metrics.png"
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
        logger.info(f"RAG metrics plot saved to {save_path}")
    
    def plot_human_eval_scores(
        self,
        results_file: str,
        save_path: str = None
    ) -> None:
        """
        Plot human evaluation scores with error bars.
        
        Args:
            results_file: Path to human evaluation results JSON
            save_path: Path to save figure
        """
        results = load_json(results_file)
        
        # Extract dimensions
        dimensions = list(results['dimension_statistics'].keys())
        dim_names = [d.replace('_score', '').capitalize() for d in dimensions]
        means = [results['dimension_statistics'][d]['mean'] for d in dimensions]
        stds = [results['dimension_statistics'][d]['std'] for d in dimensions]
        
        # Create bar plot
        fig, ax = plt.subplots(figsize=(10, 6))
        colors = ['#3498db', '#2ecc71', '#f39c12', '#e74c3c']
        bars = ax.bar(dim_names, means, yerr=stds, capsize=8, alpha=0.7, color=colors)
        
        ax.set_ylabel('Likert Scale Score (1-5)', fontsize=14, fontweight='bold')
        ax.set_title('Human Evaluation: System Quality Assessment', 
                    fontsize=16, fontweight='bold')
        ax.set_ylim(0, 5.5)
        ax.axhline(y=4.0, color='green', linestyle='--', alpha=0.5, label='Target (4.0)')
        ax.grid(axis='y', alpha=0.3)
        ax.legend()
        
        # Add value labels
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{height:.2f}',
                   ha='center', va='bottom', fontsize=12, fontweight='bold')
        
        plt.tight_layout()
        
        if save_path is None:
            save_path = self.output_dir / "human_eval_scores.png"
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
        logger.info(f"Human evaluation plot saved to {save_path}")
    
    def plot_score_distributions(
        self,
        component_file: str,
        metric_name: str = 'BERTScore-F1',
        save_path: str = None
    ) -> None:
        """
        Plot distribution of scores across samples.
        
        Args:
            component_file: Path to component results
            metric_name: Metric to plot distribution for
            save_path: Path to save figure
        """
        results = load_json(component_file)
        scores = [item['scores'][metric_name] 
                 for item in results['detailed_results']]
        
        # Create histogram with KDE
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.hist(scores, bins=20, alpha=0.6, color='skyblue', edgecolor='black', density=True)
        
        # Add KDE
        from scipy import stats
        kde = stats.gaussian_kde(scores)
        x_range = np.linspace(min(scores), max(scores), 100)
        ax.plot(x_range, kde(x_range), 'r-', linewidth=2, label='KDE')
        
        # Add mean line
        mean_score = np.mean(scores)
        ax.axvline(mean_score, color='green', linestyle='--', linewidth=2, 
                  label=f'Mean: {mean_score:.3f}')
        
        ax.set_xlabel(f'{metric_name} Score', fontsize=14, fontweight='bold')
        ax.set_ylabel('Density', fontsize=14, fontweight='bold')
        ax.set_title(f'Distribution of {metric_name} Scores', 
                    fontsize=16, fontweight='bold')
        ax.legend()
        ax.grid(alpha=0.3)
        
        plt.tight_layout()
        
        if save_path is None:
            save_path = self.output_dir / f"distribution_{metric_name}.png"
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
        logger.info(f"Distribution plot saved to {save_path}")
    
    def create_comparison_table(
        self,
        component_file: str,
        rag_file: str,
        human_file: str = None,
        save_path: str = None
    ) -> pd.DataFrame:
        """
        Create comparison table of all metrics.
        
        Args:
            component_file: Component results
            rag_file: RAG results  
            human_file: Human evaluation results (optional)
            save_path: Path to save CSV
            
        Returns:
            Pandas DataFrame with all metrics
        """
        comp_results = load_json(component_file)
        rag_results = load_json(rag_file)
        
        data = {
            'Category': [],
            'Metric': [],
            'Score': [],
            'Std': []
        }
        
        # Component metrics
        for metric, stats in comp_results['aggregated_scores'].items():
            data['Category'].append('Component-Level')
            data['Metric'].append(metric)
            data['Score'].append(stats['mean'])
            data['Std'].append(stats['std'])
        
        # RAG metrics
        for metric, stats in rag_results['metric_statistics'].items():
            data['Category'].append('RAG System')
            data['Metric'].append(metric)
            data['Score'].append(stats['mean'])
            data['Std'].append(stats['std'])
        
        # Human evaluation
        if human_file:
            human_results = load_json(human_file)
            for dim, stats in human_results['dimension_statistics'].items():
                data['Category'].append('Human Evaluation')
                data['Metric'].append(dim.replace('_score', ''))
                data['Score'].append(stats['mean'])
                data['Std'].append(stats['std'])
        
        df = pd.DataFrame(data)
        
        if save_path is None:
            save_path = self.output_dir / "comparison_table.csv"
        df.to_csv(save_path, index=False)
        logger.info(f"Comparison table saved to {save_path}")
        
        return df


def generate_all_visualizations(
    component_file: str,
    rag_file: str,
    human_file: str = None,
    output_dir: str = "../results/figures"
) -> None:
    """
    Generate all visualization plots.
    
    Args:
        component_file: Component evaluation results
        rag_file: RAG evaluation results
        human_file: Human evaluation results (optional)
        output_dir: Directory to save figures
    """
    vis = EvaluationVisualizer(output_dir)
    
    logger.info("Generating visualizations...")
    
    vis.plot_component_metrics(component_file)
    vis.plot_rag_metrics(rag_file)
    
    if human_file:
        vis.plot_human_eval_scores(human_file)
    
    vis.plot_score_distributions(component_file, 'BERTScore-F1')
    vis.create_comparison_table(component_file, rag_file, human_file)
    
    logger.info(f"All visualizations saved to {output_dir}")


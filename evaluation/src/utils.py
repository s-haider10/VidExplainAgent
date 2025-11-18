"""
Utility functions for the evaluation framework.
"""

import json
import os
from typing import Dict, List, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_json(file_path: str) -> Dict[str, Any]:
    """Load JSON file and return data."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {file_path}: {e}")
        raise


def save_json(data: Dict[str, Any], file_path: str) -> None:
    """Save data to JSON file."""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved results to {file_path}")


def calculate_confidence_interval(
    scores: List[float], 
    confidence: float = 0.95
) -> tuple[float, float]:
    """Calculate confidence interval for a list of scores."""
    import numpy as np
    from scipy import stats
    
    mean = np.mean(scores)
    stderr = stats.sem(scores)
    interval = stderr * stats.t.ppf((1 + confidence) / 2., len(scores) - 1)
    
    return mean - interval, mean + interval


def calculate_statistics(scores: List[float]) -> Dict[str, float]:
    """Calculate descriptive statistics for scores."""
    import numpy as np
    
    return {
        "mean": float(np.mean(scores)),
        "median": float(np.median(scores)),
        "std": float(np.std(scores)),
        "min": float(np.min(scores)),
        "max": float(np.max(scores)),
        "count": len(scores)
    }


def format_latex_table(
    data: Dict[str, Dict[str, float]], 
    caption: str = "Evaluation Results"
) -> str:
    """Format results as a LaTeX table."""
    latex = "\\begin{table}[h]\n"
    latex += "\\centering\n"
    latex += f"\\caption{{{caption}}}\n"
    latex += "\\begin{tabular}{l" + "c" * len(next(iter(data.values()))) + "}\n"
    latex += "\\hline\n"
    
    # Header
    headers = ["Metric"] + list(next(iter(data.values())).keys())
    latex += " & ".join(headers) + " \\\\\n"
    latex += "\\hline\n"
    
    # Data rows
    for metric, values in data.items():
        row = [metric] + [f"{v:.4f}" for v in values.values()]
        latex += " & ".join(row) + " \\\\\n"
    
    latex += "\\hline\n"
    latex += "\\end{tabular}\n"
    latex += "\\end{table}\n"
    
    return latex


def ensure_nltk_data():
    """Download required NLTK data if not present."""
    import nltk
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        logger.info("Downloading NLTK punkt tokenizer...")
        nltk.download('punkt', quiet=True)
    
    try:
        nltk.data.find('corpora/wordnet')
    except LookupError:
        logger.info("Downloading NLTK wordnet...")
        nltk.download('wordnet', quiet=True)


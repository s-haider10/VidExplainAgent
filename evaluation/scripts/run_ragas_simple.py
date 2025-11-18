#!/usr/bin/env python3
"""
Simplified RAGAS Evaluation using Direct Metric Scoring

Based on RAGAS 0.3+ tutorial approach with custom metrics.
"""

import sys
import json
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import asyncio
from dotenv import load_dotenv
from ragas.llms import llm_factory
from ragas.metrics import DiscreteMetric
from openai import AsyncOpenAI
from tqdm import tqdm

# Load .env file
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
    print(f"✅ Loaded environment from {env_path}")

# Initialize LLM using the new API with async client
openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
llm = llm_factory("gpt-4o-mini", client=openai_client)

# Define custom metrics based on RAGAS framework
answer_relevancy_metric = DiscreteMetric(
    name="answer_relevancy",
    prompt="""Evaluate if the answer is relevant to the question.
Question: {question}
Answer: {answer}
Ground Truth: {ground_truth}

Return 'pass' if the answer addresses the question appropriately, 'fail' otherwise.""",
    allowed_values=["pass", "fail"],
)

answer_correctness_metric = DiscreteMetric(
    name="answer_correctness",
    prompt="""Evaluate if the answer is factually correct compared to the ground truth.
Question: {question}
Answer: {answer}
Ground Truth: {ground_truth}

Return 'pass' if the answer is factually correct, 'fail' otherwise.""",
    allowed_values=["pass", "fail"],
)

answer_faithfulness_metric = DiscreteMetric(
    name="answer_faithfulness",
    prompt="""Evaluate if the answer is faithful to the retrieved context (not hallucinated).
Question: {question}
Answer: {answer}
Retrieved Context: {context}

Return 'pass' if the answer is grounded in the context, 'fail' if it contains unsupported claims.""",
    allowed_values=["pass", "fail"],
)

context_relevance_metric = DiscreteMetric(
    name="context_relevance",
    prompt="""Evaluate if the retrieved context is relevant to answering the question.
Question: {question}
Retrieved Context: {context}

Return 'pass' if the context is relevant, 'fail' otherwise.""",
    allowed_values=["pass", "fail"],
)


async def evaluate_single_response(qa_item, system_response):
    """Evaluate a single Q&A response with all metrics."""
    
    question = qa_item['question']
    ground_truth = qa_item['ground_truth_answer']
    answer = system_response.get('answer', '')
    
    # Get context - prefer retrieved_contexts, fallback to ground_truth_context
    retrieved_contexts = system_response.get('retrieved_contexts', [])
    if not retrieved_contexts:
        retrieved_contexts = qa_item.get('ground_truth_context', [])
    
    context = ' '.join(retrieved_contexts) if isinstance(retrieved_contexts, list) else str(retrieved_contexts)
    
    results = {
        'question_id': qa_item['id'],
        'question': question,
    }
    
    # Skip if no answer
    if not answer or answer.strip() == '':
        results.update({
            'answer_relevancy': 'fail',
            'answer_correctness': 'fail',
            'answer_faithfulness': 'fail',
            'context_relevance': 'fail',
            'note': 'No answer generated'
        })
        return results
    
    # Answer Relevancy
    try:
        score = await answer_relevancy_metric.ascore(
            llm=llm,
            question=question,
            answer=answer,
            ground_truth=ground_truth
        )
        results['answer_relevancy'] = score.value
    except Exception as e:
        results['answer_relevancy'] = 'error'
        print(f"  ⚠️ Answer Relevancy error: {e}")
    
    # Answer Correctness
    try:
        score = await answer_correctness_metric.ascore(
            llm=llm,
            question=question,
            answer=answer,
            ground_truth=ground_truth
        )
        results['answer_correctness'] = score.value
    except Exception as e:
        results['answer_correctness'] = 'error'
        print(f"  ⚠️ Answer Correctness error: {e}")
    
    # Answer Faithfulness (only if context available)
    if context.strip():
        try:
            score = await answer_faithfulness_metric.ascore(
                llm=llm,
                question=question,
                answer=answer,
                context=context
            )
            results['answer_faithfulness'] = score.value
        except Exception as e:
            results['answer_faithfulness'] = 'error'
            print(f"  ⚠️ Answer Faithfulness error: {e}")
    else:
        results['answer_faithfulness'] = 'no_context'
    
    # Context Relevance
    if context.strip():
        try:
            score = await context_relevance_metric.ascore(
                llm=llm,
                question=question,
                context=context
            )
            results['context_relevance'] = score.value
        except Exception as e:
            results['context_relevance'] = 'error'
            print(f"  ⚠️ Context Relevance error: {e}")
    else:
        results['context_relevance'] = 'no_context'
    
    return results


async def run_evaluation(qa_pairs_path, system_responses_path, output_path):
    """Run complete RAGAS evaluation."""
    
    print("\n" + "="*70)
    print("RAGAS EVALUATION (Simplified Approach)")
    print("="*70)
    
    # Load data
    print(f"\n📂 Loading data...")
    with open(qa_pairs_path, 'r') as f:
        qa_data = json.load(f)
    with open(system_responses_path, 'r') as f:
        system_data = json.load(f)
    
    qa_pairs = qa_data['qa_pairs']
    responses = {r['question_id']: r for r in system_data['responses']}
    
    print(f"   ✅ Loaded {len(qa_pairs)} Q&A pairs")
    print(f"   ✅ Loaded {len(responses)} system responses")
    
    # Match and evaluate
    print(f"\n🔬 Evaluating responses...")
    all_results = []
    
    for qa in tqdm(qa_pairs, desc="Evaluating"):
        qa_id = qa['id']
        if qa_id in responses:
            result = await evaluate_single_response(qa, responses[qa_id])
            all_results.append(result)
        else:
            print(f"  ⚠️ No response found for {qa_id}")
    
    # Calculate statistics
    print(f"\n📊 Calculating statistics...")
    
    metrics = ['answer_relevancy', 'answer_correctness', 'answer_faithfulness', 'context_relevance']
    stats = {}
    
    for metric in metrics:
        values = [r[metric] for r in all_results if r.get(metric) == 'pass' or r.get(metric) == 'fail']
        if values:
            pass_count = sum(1 for v in values if v == 'pass')
            fail_count = sum(1 for v in values if v == 'fail')
            total = len(values)
            pass_rate = pass_count / total if total > 0 else 0
            
            stats[metric] = {
                'pass_count': pass_count,
                'fail_count': fail_count,
                'total_evaluated': total,
                'pass_rate': pass_rate,
                'score': pass_rate  # Convert to 0-1 score
            }
        else:
            stats[metric] = {
                'pass_count': 0,
                'fail_count': 0,
                'total_evaluated': 0,
                'pass_rate': 0.0,
                'score': 0.0
            }
    
    # Prepare output
    output = {
        'num_samples': len(all_results),
        'metrics_summary': stats,
        'detailed_results': all_results,
        'overall_pass_rate': sum(s['pass_rate'] for s in stats.values()) / len(stats) if stats else 0
    }
    
    # Save results
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\n✅ Results saved to: {output_path}")
    
    # Print summary
    print("\n" + "="*70)
    print("EVALUATION SUMMARY")
    print("="*70)
    print(f"\nEvaluated: {len(all_results)} responses\n")
    
    for metric, stat in stats.items():
        print(f"{metric:25s}: {stat['pass_rate']:.1%} ({stat['pass_count']}/{stat['total_evaluated']} pass)")
    
    print(f"\n{'Overall Pass Rate':25s}: {output['overall_pass_rate']:.1%}")
    print("\n" + "="*70)
    
    return output


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run simplified RAGAS evaluation")
    parser.add_argument("--qa-pairs", required=True, help="Path to Q&A pairs JSON")
    parser.add_argument("--system-responses", required=True, help="Path to system responses JSON")
    parser.add_argument("--output", default="../results/ragas_scores.json", help="Output path")
    
    args = parser.parse_args()
    
    try:
        results = asyncio.run(run_evaluation(
            args.qa_pairs,
            args.system_responses,
            args.output
        ))
        print("\n🎉 RAGAS evaluation complete!")
    except Exception as e:
        print(f"\n❌ Evaluation failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


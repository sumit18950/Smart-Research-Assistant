"""
Standalone RAGAS evaluation script.
Run this to evaluate the RAG system with sample queries.

Usage:
    cd backend
    python -m evaluation.run_evaluation
"""

import asyncio
import json
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.services.vector_store import create_vector_store
from app.services.llm_service import LLMService
from app.services.agent_workflow import ResearchAgent
from app.services.evaluator import RAGEvaluator
from app.models.schemas import QueryRequest


# Sample evaluation dataset
EVAL_QUERIES = [
    "What are the main contributions of the paper?",
    "What methodology was used in the study?",
    "What are the key findings and results?",
    "What limitations does the study acknowledge?",
    "How does this work compare to prior research?",
]

GROUND_TRUTHS = [
    "The paper presents a novel approach to...",
    "The study uses a mixed-methods approach combining...",
    "Key findings include significant improvements in...",
    "The study acknowledges limitations in sample size and...",
    "Compared to prior work, this approach improves upon...",
]


async def main():
    print("=" * 60)
    print("RAGAS Evaluation Pipeline")
    print("=" * 60)

    # Initialize components
    vector_store = create_vector_store()
    llm_service = LLMService()
    agent = ResearchAgent(vector_store, llm_service)

    doc_count = vector_store.document_count()
    print(f"\nDocuments in vector store: {doc_count}")

    if doc_count == 0:
        print("WARNING: No documents in vector store. Upload documents first.")
        print("Running evaluation anyway (results will reflect empty context).\n")

    # Run evaluation
    evaluator = RAGEvaluator(agent)
    print(f"Running evaluation on {len(EVAL_QUERIES)} queries...\n")

    result = await evaluator.evaluate(
        queries=EVAL_QUERIES,
        ground_truths=GROUND_TRUTHS,
    )

    # Print results
    print("\n" + "=" * 60)
    print("EVALUATION RESULTS")
    print("=" * 60)
    print(f"  Faithfulness:       {result.faithfulness:.3f}")
    print(f"  Answer Relevancy:   {result.answer_relevancy:.3f}")
    print(f"  Context Precision:  {result.context_precision:.3f}")
    if result.context_recall is not None:
        print(f"  Context Recall:     {result.context_recall:.3f}")
    print(f"  Overall Score:      {result.overall_score:.3f}")
    print("=" * 60)

    # Save results to file
    output = {
        "faithfulness": result.faithfulness,
        "answer_relevancy": result.answer_relevancy,
        "context_precision": result.context_precision,
        "context_recall": result.context_recall,
        "overall_score": result.overall_score,
        "per_query_scores": result.per_query_scores,
    }

    output_path = os.path.join(os.path.dirname(__file__), "results.json")
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\nDetailed results saved to: {output_path}")


if __name__ == "__main__":
    asyncio.run(main())

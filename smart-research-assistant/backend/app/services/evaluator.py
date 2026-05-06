"""
RAGAS evaluation pipeline for measuring RAG system quality.

Metrics:
- Faithfulness: Is the answer grounded in the retrieved context?
- Answer Relevancy: Does the answer address the question?
- Context Precision: Are the retrieved chunks relevant to the query?
- Context Recall: Does the context contain all needed information?
"""

from datasets import Dataset
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall,
)

from app.core.logging import logger
from app.models.schemas import EvaluationResult, QueryRequest
from app.services.agent_workflow import ResearchAgent


class RAGEvaluator:
    def __init__(self, agent: ResearchAgent):
        self.agent = agent

    async def evaluate(
        self,
        queries: list[str],
        ground_truths: list[str] | None = None,
    ) -> EvaluationResult:
        """
        Run RAGAS evaluation on a set of queries.
        If ground_truths are provided, context_recall is also computed.
        """
        logger.info(f"Starting RAGAS evaluation on {len(queries)} queries")

        questions = []
        answers = []
        contexts = []
        gt_list = []

        for i, query in enumerate(queries):
            # Run query through the full pipeline
            request = QueryRequest(query=query, top_k=5)
            response = await self.agent.run(request)

            questions.append(query)
            answers.append(response.answer)

            # Collect context from sources
            ctx = [s.snippet for s in response.sources]
            contexts.append(ctx if ctx else ["No context retrieved."])

            if ground_truths and i < len(ground_truths):
                gt_list.append(ground_truths[i])

        # Build RAGAS dataset
        eval_data = {
            "question": questions,
            "answer": answers,
            "contexts": contexts,
        }

        metrics = [faithfulness, answer_relevancy, context_precision]

        if gt_list and len(gt_list) == len(queries):
            eval_data["ground_truth"] = gt_list
            metrics.append(context_recall)

        dataset = Dataset.from_dict(eval_data)

        # Run RAGAS evaluation
        result = evaluate(dataset=dataset, metrics=metrics)
        scores = result.to_pandas()

        # Calculate per-query scores
        per_query = []
        for _, row in scores.iterrows():
            per_query.append({
                "question": row.get("question", ""),
                "faithfulness": round(row.get("faithfulness", 0), 3),
                "answer_relevancy": round(row.get("answer_relevancy", 0), 3),
                "context_precision": round(row.get("context_precision", 0), 3),
            })

        avg_faith = scores["faithfulness"].mean()
        avg_relevancy = scores["answer_relevancy"].mean()
        avg_precision = scores["context_precision"].mean()
        avg_recall = scores["context_recall"].mean() if "context_recall" in scores else None

        overall = (avg_faith + avg_relevancy + avg_precision) / 3
        if avg_recall is not None:
            overall = (avg_faith + avg_relevancy + avg_precision + avg_recall) / 4

        logger.info(
            f"RAGAS evaluation complete: faithfulness={avg_faith:.3f}, "
            f"relevancy={avg_relevancy:.3f}, precision={avg_precision:.3f}"
        )

        return EvaluationResult(
            faithfulness=round(avg_faith, 3),
            answer_relevancy=round(avg_relevancy, 3),
            context_precision=round(avg_precision, 3),
            context_recall=round(avg_recall, 3) if avg_recall is not None else None,
            overall_score=round(overall, 3),
            per_query_scores=per_query,
        )

import json
import os
from typing import Dict, Any, List
from backend.config import EVALUATION_DATASET_PATH
from backend.ranking_service import ranking_service
from backend.resume_parser import parse_jd_content, parse_resume_content

class EvaluationModule:
    def evaluate_benchmark(self, dataset_path: str = None) -> Dict[str, Any]:
        """
        Evaluates system predictions against ground-truth manually labeled evaluation dataset.
        Calculates Precision, Recall, F1-Score, and Top-K Ranking Accuracy dynamically.
        """
        file_path = dataset_path or EVALUATION_DATASET_PATH
        if not os.path.exists(file_path):
            return {
                "error": f"Evaluation dataset not found at {file_path}",
                "metrics": {}
            }

        with open(file_path, "r", encoding="utf-8") as f:
            test_cases = json.load(f)

        tp, fp, fn, tn = 0, 0, 0, 0
        top1_hits = 0
        top3_hits = 0
        total_jds = len(test_cases)
        
        detailed_eval_results = []

        for case in test_cases:
            jd_title = case.get("job_title", "Position")
            jd_text = case.get("jd_text", "")
            candidates = case.get("candidates", [])
            
            # Parse JD & Resumes using system pipeline
            parsed_jd = parse_jd_content(jd_text, title=jd_title)
            parsed_resumes = [
                parse_resume_content(cand["resume_text"], filename=cand["name"])
                for cand in candidates
            ]
            
            # Run model predictions
            predictions = ranking_service.rank_candidates(parsed_jd, parsed_resumes)
            
            # Map ground truth labels
            ground_truth_map = {cand["name"]: cand.get("ground_truth_relevant", False) for cand in candidates}
            ground_truth_top = case.get("ground_truth_top_candidate", "")

            # Check Top-K Accuracy
            pred_top_1 = predictions[0]["candidate_name"] if predictions else ""
            pred_top_3 = [p["candidate_name"] for p in predictions[:3]] if len(predictions) >= 3 else [p["candidate_name"] for p in predictions]

            if pred_top_1 == ground_truth_top:
                top1_hits += 1
            if ground_truth_top in pred_top_3:
                top3_hits += 1

            # Classification metrics at threshold (Score >= 50% is considered Relevant)
            for pred in predictions:
                c_name = pred["candidate_name"]
                pred_relevant = pred["overall_match_percentage"] >= 50
                actual_relevant = ground_truth_map.get(c_name, False)


                if pred_relevant and actual_relevant:
                    tp += 1
                elif pred_relevant and not actual_relevant:
                    fp += 1
                elif not pred_relevant and actual_relevant:
                    fn += 1
                else:
                    tn += 1

            detailed_eval_results.append({
                "job_title": jd_title,
                "ground_truth_top": ground_truth_top,
                "predicted_top": pred_top_1,
                "top_1_matched": pred_top_1 == ground_truth_top,
                "top_3_matched": ground_truth_top in pred_top_3
            })

        # Calculate metrics
        precision = float(tp / (tp + fp)) if (tp + fp) > 0 else 0.0
        recall = float(tp / (tp + fn)) if (tp + fn) > 0 else 0.0
        f1_score = float(2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0
        top1_accuracy = float(top1_hits / total_jds) if total_jds > 0 else 0.0
        top3_accuracy = float(top3_hits / total_jds) if total_jds > 0 else 0.0

        return {
            "total_test_jobs": total_jds,
            "total_evaluated_pairs": tp + fp + fn + tn,
            "confusion_matrix": {"TP": tp, "FP": fp, "FN": fn, "TN": tn},
            "metrics": {
                "precision": round(precision, 4),
                "recall": round(recall, 4),
                "f1_score": round(f1_score, 4),
                "top_1_accuracy": round(top1_accuracy, 4),
                "top_3_accuracy": round(top3_accuracy, 4)
            },
            "case_breakdown": detailed_eval_results
        }

evaluation_module = EvaluationModule()

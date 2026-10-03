"""Sentiment evaluation metrics computation against ground truth labels."""

from typing import Any, Dict, List, Optional

from sklearn.metrics import classification_report, confusion_matrix


def evaluate_sentiment_predictions(
    y_true: List[str],
    y_pred: List[str],
    labels: Optional[List[str]] = None,
) -> Optional[Dict[str, Any]]:
    """Compute classification metrics ONLY when ground-truth labels exist.

    Returns None if y_true is empty or contains no valid ground-truth labels.
    """
    if not y_true or not y_pred or len(y_true) != len(y_pred):
        return None

    # Filter out empty or None ground truth
    valid_pairs = [(t.lower(), p.lower()) for t, p in zip(y_true, y_pred) if t]
    if not valid_pairs:
        return None

    if labels is None:
        target_labels = ["negative", "neutral", "positive"]
    else:
        target_labels = [label.lower() for label in labels]

    filtered_true = [t for t, p in valid_pairs]
    filtered_pred = [p for t, p in valid_pairs]

    report = classification_report(
        filtered_true,
        filtered_pred,
        labels=target_labels,
        output_dict=True,
        zero_division=0,
    )
    conf_matrix = confusion_matrix(
        filtered_true,
        filtered_pred,
        labels=target_labels,
    ).tolist()

    return {
        "accuracy": round(float(report.get("accuracy", 0.0)), 4),
        "macro_f1": round(float(report.get("macro avg", {}).get("f1-score", 0.0)), 4),
        "weighted_f1": round(float(report.get("weighted avg", {}).get("f1-score", 0.0)), 4),
        "per_class": {
            label: {
                "precision": round(float(report.get(label, {}).get("precision", 0.0)), 4),
                "recall": round(float(report.get(label, {}).get("recall", 0.0)), 4),
                "f1": round(float(report.get(label, {}).get("f1-score", 0.0)), 4),
                "support": int(report.get(label, {}).get("support", 0)),
            }
            for label in target_labels
            if label in report
        },
        "confusion_matrix": {
            "labels": target_labels,
            "matrix": conf_matrix,
        },
        "sample_count": len(valid_pairs),
    }

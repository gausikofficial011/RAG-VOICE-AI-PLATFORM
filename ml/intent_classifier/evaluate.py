"""
Evaluation Script for Query Intent Classifier
"""

import json
import os
import joblib
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix


def evaluate():
    artifact_path = "ml/artifacts/intent_classifier.joblib"
    dataset_path = "ml/datasets/intent_dataset.json"

    if not os.path.exists(artifact_path):
        raise FileNotFoundError(f"Model artifact not found at {artifact_path}. Run train.py first.")

    model = joblib.load(artifact_path)
    with open(dataset_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    texts = [item["text"] for item in data]
    labels = [item["intent"] for item in data]

    preds = model.predict(texts)
    acc = accuracy_score(labels, preds)
    cm = confusion_matrix(labels, preds)

    print("=========================================")
    print("QUERY INTENT CLASSIFIER EVALUATION REPORT")
    print("=========================================")
    print(f"Total Samples: {len(texts)}")
    print(f"Accuracy: {acc:.4f}\n")
    print(classification_report(labels, preds, zero_division=0))
    print("Confusion Matrix:")
    print(cm)

    return {"accuracy": acc, "total_samples": len(texts)}


if __name__ == "__main__":
    evaluate()

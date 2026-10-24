"""
Training Script for Query Intent Classifier
"""

import json
import os
import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report, accuracy_score, precision_recall_fscore_support, confusion_matrix


def train():
    os.makedirs("ml/artifacts", exist_ok=True)
    dataset_path = "ml/datasets/intent_dataset.json"
    with open(dataset_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    texts = [item["text"] for item in data]
    labels = [item["intent"] for item in data]

    # Pipeline: TF-IDF n-grams + Logistic Regression
    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2), max_features=5000)),
        ("clf", LogisticRegression(C=1.0, max_iter=500, random_state=42)),
    ])

    print(f"Training Intent Classifier on {len(texts)} samples across {len(set(labels))} classes...")
    pipeline.fit(texts, labels)

    # Evaluate on training data
    preds = pipeline.predict(texts)
    acc = float(accuracy_score(labels, preds))
    precision, recall, f1, _ = precision_recall_fscore_support(labels, preds, average="weighted", zero_division=0)
    cm = confusion_matrix(labels, preds).tolist()

    unique_labels = sorted(list(set(labels)))
    report = classification_report(labels, preds, output_dict=True, zero_division=0)

    metrics = {
        "model_name": "query_intent_classifier",
        "version": "v1.0.0",
        "samples": len(texts),
        "classes": unique_labels,
        "accuracy": round(acc, 4),
        "precision": round(float(precision), 4),
        "recall": round(float(recall), 4),
        "f1": round(float(f1), 4),
        "confusion_matrix": cm,
        "classification_report": report,
    }

    model_save_path = "ml/artifacts/intent_classifier.joblib"
    metrics_save_path = "ml/artifacts/intent_classifier_metrics.json"

    joblib.dump(pipeline, model_save_path)
    with open(metrics_save_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    print(f"Training completed successfully!")
    print(f"Accuracy: {acc:.4f} | F1: {f1:.4f}")
    print(f"Saved artifact to {model_save_path}")
    print(f"Saved metrics to {metrics_save_path}")
    return metrics


if __name__ == "__main__":
    train()

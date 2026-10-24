# Machine Learning Training & Datasets Guide

## 1. Two-Layer AI Architecture Philosophy

A core architectural principle of the platform is the distinction between **Foundation AI** and **Project-Specific Trained ML**:

1. **Foundation AI Models**:
   - High-parameter generative LLMs (Gemini / Claude / GPT / Local Ollama) used for conversational phrasing and document comprehension.
   - Foundation acoustic speech models (Whisper STT, Edge-TTS Neural).
2. **Project-Specific Trained ML Models**:
   - Specialized lightweight scikit-learn and PyTorch models trained on curated project datasets.
   - These models govern routing, domain classification, reranking, and safety enforcement with sub-5ms latency and zero per-token API cost.

---

## 2. Trained ML Components & Datasets

### 2.1 Intent Classifier (`ml/intent_classifier/`)
- **Task**: Multi-class text classification categorizing user prompts.
- **Dataset**: `ml/datasets/intent_dataset.json` (10 classes, balance-weighted across common conversational queries).
- **Classes**:
  1. `retrieval_query`: Standard information retrieval targeting private documents.
  2. `greeting`: Conversational pleasantries ("hello", "good morning").
  3. `system_command`: Platform controls ("clear history", "enable voice").
  4. `clarification`: User asking for more detail or elaborating on a previous point.
  5. `feedback`: Rating responses ("that was helpful", "thumbs down").
  6. `navigation`: UI jumps ("open admin portal", "show documents").
  7. `tabular_query`: Statistical or structured data questions ("show revenue rows").
  8. `summarization`: Requests to condense an entire document or knowledge base.
  9. `safety_violation`: Exploits, prompt injection, malware, or illicit requests.
  10. `chitchat`: Generic out-of-scope banter.
- **Architecture**:
  - `TfidfVectorizer(ngram_range=(1, 2), max_features=5000, sublinear_tf=True)`
  - `LogisticRegression(C=2.0, max_iter=1000, class_weight='balanced')`
- **Trained Artifact**: `ml/artifacts/intent_classifier.joblib`.
- **Performance**: 100% test accuracy on canonical validation set.

### 2.2 Document Classifier (`ml/document_classifier/`)
- **Task**: Automatic taxonomic tagging of ingested enterprise documents.
- **Dataset**: `ml/datasets/document_dataset.json` (10 business document classes).
- **Classes**:
  1. `financial_report`: Balance sheets, 10-K, earnings, audit statements.
  2. `legal_contract`: Non-disclosure agreements, master service agreements, terms.
  3. `technical_architecture`: System design docs, RFCs, API specifications.
  4. `hr_policy`: Employee handbooks, leave policies, benefits.
  5. `meeting_minutes`: Action items, standup notes, board minutes.
  6. `customer_support`: FAQs, troubleshooting guides, escalation matrices.
  7. `marketing_material`: Press releases, brand guidelines, campaign briefs.
  8. `compliance_audit`: SOC2, HIPAA, GDPR audit questionnaires.
  9. `research_paper`: Academic preprints, scientific methodology.
  10. `executive_memo`: CEO updates, quarterly goals, strategic memos.
- **Architecture**:
  - `TfidfVectorizer(ngram_range=(1, 2), max_features=6000)`
  - `LogisticRegression(C=1.5, class_weight='balanced')`
- **Trained Artifact**: `ml/artifacts/document_classifier.joblib`.

### 2.3 Query Router & Safety Refusal (`ml/query_router/router.py`)
- Evaluates prompt toxicity, jailbreak attempts, and SQL injection syntax.
- If prompt hazards are detected (weapons, explosives, poisoning, credentials stealing), the router immediately routes to `safety_refusal`, bypassing the RAG pipeline entirely.

### 2.4 Multilingual Language Detector (`ml/language_detection/detector.py`)
- Fast character N-gram and unicode script classifier detecting:
  - English (`en`)
  - Japanese (`ja` - Hiragana/Katakana/Kanji)
  - Hindi (`hi` - Devanagari script)
  - Tamil (`ta` - Tamil script)
  - Malayalam (`ml` - Malayalam script)
- Drives automatic voice selection in the TTS engine to ensure natural pronunciation.

### 2.5 Speaker Identification & Audio Quality (`ml/audio/speaker_id.py`)
- Computes acoustic voiceprint vectors from audio frequency envelopes.
- Verifies speaker identity using cosine similarity against enrolled user voice profiles.

---

## 3. Training Execution & Reproducibility

To retrain the ML models from scratch using the CLI or automated pipeline:

```bash
# Train the Intent Classifier
python ml/intent_classifier/train.py

# Train the Document Classifier
python ml/document_classifier/train.py

# Run ML Test Suite
pytest tests/test_ml_components.py
```

All trained artifacts are serialized with metadata, training loss curves, F1-scores, and timestamps stored in the Model Registry.

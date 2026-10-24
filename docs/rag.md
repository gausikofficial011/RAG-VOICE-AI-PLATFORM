# Retrieval-Augmented Generation (RAG) Guide

## 1. Pipeline Overview

The RAG pipeline implements an enterprise multi-stage retrieval architecture designed for high precision, sub-second latency, and verifiable grounding:

```
[User Query]
     |
     v
[1. Intent & Safety Routing] ──(Unsafe)──> [Refusal: Safety Policy]
     | (Safe)
     v
[2. Hybrid Retrieval]
     ├──> Sparse Search (BM25 Lexical Keyword Matching)
     └──> Dense Search (Cosine Distance via Qdrant Vectors)
     |
     v
[3. Reciprocal Rank Fusion (RRF)] ──> Merged Rank List
     |
     v
[4. Cross-Encoder Reranking] ──> Precision Top-K Relevant Passages
     |
     v
[5. LLM Synthesis with Grounded Context]
     |
     v
[6. Hallucination & Grounding Verification]
     ├──> PASS (Score >= 0.70) ──> Return Answer + Citations + Latency Trace
     └──> FAIL (Score < 0.70)  ──> "Evidence insufficient to substantiate claim."
```

---

## 2. Document Processing & Ingestion

The platform supports ingestion of `.pdf`, `.docx`, `.txt`, `.csv`, `.md`, `.html`, and `.json` documents.

### 2.1 Parsing Strategies
- **PDF**: PyPDF / PDFMiner text extraction preserving page boundaries for accurate page citations.
- **DOCX**: `python-docx` paragraph and table cell extraction.
- **CSV**: Processed into both chunkable text representations and structured rows for Table RAG.
- **HTML/Markdown**: Tag stripping with structural heading preservation.

### 2.2 Structure-Aware Chunking
Chunks are generated using a sliding-window tokenizer:
- Default `chunk_size`: 500 tokens (~2,000 characters).
- Default `chunk_overlap`: 80 tokens (~320 characters).
- Boundaries prioritize paragraph breaks (`\n\n`), sentence boundaries (`. `), and heading transitions to prevent semantic truncation.
- Each chunk maintains metadata:
  ```json
  {
    "document_id": "doc_a1b2c3",
    "organization_id": "org_xyz",
    "knowledge_base_id": "kb_123",
    "chunk_index": 4,
    "page_number": 2,
    "heading_context": "Section 4.1: Security Standards"
  }
  ```

---

## 3. Hybrid Retrieval & Reciprocal Rank Fusion (RRF)

Pure dense semantic search often struggles with precise acronyms, identifiers, and exact numerical figures (e.g., "CVE-2024-3094" or "Model 9X-B"). Pure BM25 struggles with synonymy and natural phrasing.

The platform executes **both in parallel** and merges their candidate lists using Reciprocal Rank Fusion:

$$RRF(d) = \sum_{m \in M} \frac{1}{k + r_m(d)}$$

Where:
- $M = \{\text{Dense}, \text{BM25}\}$
- $r_m(d)$ is the rank position of document chunk $d$ in system $m$ (1-indexed).
- $k = 60$ (smoothing constant preventing high-rank dominance).

---

## 4. Cross-Encoder Reranking

Candidate chunks from RRF (default Top 15) are passed to a Cross-Encoder Reranker. Unlike bi-encoders that encode query and document separately, the cross-encoder performs joint cross-attention across the query and chunk tokens:

$$\text{Score}(q, d) = \sigma(\mathbf{W} \cdot \text{Transformer}([CLS] \circ q \circ [SEP] \circ d))$$

### Evaluation Metrics Implemented
The reranker service calculates retrieval performance metrics on benchmark datasets:
- **Mean Reciprocal Rank (MRR)**: Average reciprocal rank of the first relevant document.
- **NDCG@K**: Normalized Discounted Cumulative Gain penalizing low-ranked relevant documents.
- **Recall@K & Precision@K**: Completeness and purity of the top-K retrieved set.

---

## 5. Grounding & Hallucination Prevention Engine

The platform enforces a strict claim-validation rule: **no answer may be returned if it cannot be anchored to retrieved evidence chunks**.

### Verification Algorithm:
1. **Sentence Decomposition**: The generated response is parsed into individual claim sentences.
2. **N-Gram Overlap & Semantic Coverage**: Each sentence is cross-checked against the retrieved chunk texts for lexical and conceptual overlap.
3. **Threshold Gate**:
   - `grounding_score >= 0.70`: Validated, marked `GROUNDED`.
   - `0.40 <= score < 0.70`: Flagged as `PARTIALLY_GROUNDED`, accompanied by user caution banner.
   - `score < 0.40`: Marked `UNGROUNDED`, response suppressed with standard disclaimer: *"The provided documents do not contain sufficient evidence to answer this question."*

---

## 6. Table RAG (Safe CSV/Data Queries)

When a query targets tabular datasets (e.g., "What was the revenue in Q3 2024?"), the `TableRAG` engine executes deterministic operations (filtering, aggregation, column lookup) directly against the structured data, eliminating LLM arithmetic errors and hallucinations.

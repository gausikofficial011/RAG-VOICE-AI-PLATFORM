"""
Structured Tabular Data RAG Engine
Performs safe, deterministic computations over CSV/structured tables without executing arbitrary code.
"""

from typing import Any, Dict, List, Optional
import re
import csv
import io


class TableRAGEngine:
    @staticmethod
    def is_tabular_query(query: str) -> bool:
        """Detect if the query requests statistical/tabular computations."""
        triggers = ["average", "mean", "total", "sum", "highest", "lowest", "max", "min", "count", "how many", "rows in"]
        q = query.lower()
        return any(t in q for t in triggers)

    @staticmethod
    def process_csv_table(csv_content: str, query: str) -> Optional[str]:
        """
        Safely parse CSV data and compute requested aggregations.
        """
        try:
            reader = csv.reader(io.StringIO(csv_content.strip()))
            rows = list(reader)
            if len(rows) < 2:
                return None

            headers = [h.strip().lower() for h in rows[0]]
            data_rows = rows[1:]

            q = query.lower()

            # 1. Row Count
            if "how many" in q or "count" in q or "number of rows" in q:
                return f"The table contains {len(data_rows)} records across {len(headers)} columns: {', '.join(headers)}."

            # Find target column referenced in query
            target_col_idx = None
            target_col_name = None
            for idx, h in enumerate(headers):
                if h in q:
                    target_col_idx = idx
                    target_col_name = h
                    break

            if target_col_idx is None:
                # Default to last numeric column
                for idx in reversed(range(len(headers))):
                    sample_vals = [r[idx] for r in data_rows if idx < len(r) and r[idx].replace(".", "", 1).isdigit()]
                    if len(sample_vals) > len(data_rows) * 0.5:
                        target_col_idx = idx
                        target_col_name = headers[idx]
                        break

            if target_col_idx is None:
                return None

            # Extract numeric values safely
            numeric_values = []
            for r in data_rows:
                if target_col_idx < len(r):
                    val_str = r[target_col_idx].replace("$", "").replace(",", "").strip()
                    try:
                        numeric_values.append(float(val_str))
                    except ValueError:
                        pass

            if not numeric_values:
                return None

            # Computations
            if "average" in q or "mean" in q:
                avg = sum(numeric_values) / len(numeric_values)
                return f"The average for '{target_col_name}' is {avg:.2f} across {len(numeric_values)} recorded entries."

            if "total" in q or "sum" in q:
                total = sum(numeric_values)
                return f"The total sum for '{target_col_name}' is {total:.2f} across {len(numeric_values)} recorded entries."

            if "max" in q or "highest" in q or "maximum" in q:
                m = max(numeric_values)
                return f"The highest recorded value for '{target_col_name}' is {m:.2f}."

            if "min" in q or "lowest" in q or "minimum" in q:
                m = min(numeric_values)
                return f"The lowest recorded value for '{target_col_name}' is {m:.2f}."

            return None
        except Exception:
            return None


table_rag_engine = TableRAGEngine()

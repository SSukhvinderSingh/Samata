"""
CRAG (Corrective RAG) Skill for Samata Legal Assistant.
Handles low-confidence retrieval scenarios by reformulating queries and retrying retrieval passes.
"""

from typing import Dict, List, Any, Optional
from skills.rag_pipeline import retrieve_chunks, CRAG_THRESHOLD

HMA_SYNONYMS = {
    "divorce": "dissolution of marriage Hindu Marriage Act Section 13 grounds",
    "maintenance": "alimony maintenance Section 25 interim maintenance Section 24 HMA",
    "custody": "child custody visitation rights guardianship section 26 HMA",
    "separation": "judicial separation Section 10 mutual consent Section 13B",
    "restitution": "restitution of conjugal rights Section 9 HMA"
}


def execute_crag_fallback(
    original_query: str,
    initial_top_score: float,
    session_context: Optional[str] = None
) -> Dict[str, Any]:
    """
    Reformulates query and executes a secondary retrieval pass.
    """
    reformulated = original_query
    query_lower = original_query.lower()

    # Query expansion strategy using domain terms
    expansions = []
    for key, expanded_term in HMA_SYNONYMS.items():
        if key in query_lower:
            expansions.append(expanded_term)

    if expansions:
        reformulated = f"{original_query} {' '.join(expansions)}"
    else:
        reformulated = f"{original_query} Hindu Marriage Act 1955 legal provisions"

    # Secondary retrieval pass
    res = retrieve_chunks(reformulated, top_k=5)
    secondary_chunks = res["retrieved_chunks"]
    secondary_top_score = res["top_score"]

    status = "resolved" if secondary_top_score >= CRAG_THRESHOLD else "unresolved"

    return {
        "original_query": original_query,
        "reformulated_query": reformulated,
        "secondary_chunks": secondary_chunks,
        "secondary_top_score": secondary_top_score,
        "crag_status": status
    }

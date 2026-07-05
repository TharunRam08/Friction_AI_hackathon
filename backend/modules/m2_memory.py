# backend/modules/m2_memory.py
"""
Memory Module — combines:
  1. Vector DB semantic retrieval (past decisions, customer facts, deal records)
  2. Live CRM context slice (financials, pipeline, team, customers) from crm_db.py
Both are merged into a single knowledge context string for the LLM pipeline.
"""
from data.vectordb import retrieve_memory
from data.crm_db import get_context_for_query


def get_past_context(question: str, goal: str, intent: dict = None) -> tuple:
    """
    Returns: (combined_knowledge_context, similarity_score)
    
    combined_knowledge_context is a rich string containing:
     - Semantically matched CRM entries (past decisions, deals, customers)
     - Live database metrics relevant to the query topic
    """
    search_query = f"{question} {goal}"

    # 1. Vector DB semantic retrieval — top 3 matching CRM entries
    semantic_memory, similarity_score = retrieve_memory(search_query, top_k=3)

    # 2. Extract intent keywords for CRM context lookup
    keywords = []
    if intent:
        # Pull keywords from goal and constraints
        goal_str = intent.get("goal", "")
        constraints = intent.get("constraints", [])
        keywords = goal_str.lower().split() + [c.lower() for c in constraints]
    else:
        # Fall back to words from the raw question
        keywords = question.lower().split()

    # 3. Live CRM database context (structured metrics)
    live_context = get_context_for_query(keywords)

    # 4. Merge both into a unified knowledge string
    combined = (
        f"[SEMANTIC MATCH FROM KNOWLEDGE BASE]\n{semantic_memory}\n\n"
        f"[LIVE CRM METRICS]\n{live_context}"
    )

    return combined, similarity_score

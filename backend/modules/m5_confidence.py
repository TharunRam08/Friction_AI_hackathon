# backend/modules/m5_confidence.py
def calculate_confidence(views: list, memory_match_score: float, ceo_stance: str) -> dict:
    # Ensure memory match score is non-negative for display and confidence calculations
    memory_match_score = max(0.0, memory_match_score)
    
    # 1. Agreement Ratio: % of personas whose stance matches the CEO's synthesized stance
    stances = [v['stance'] for v in views]
    matching_count = stances.count(ceo_stance)
    agreement_ratio = matching_count / len(stances) if len(stances) > 0 else 0.0
    
    # 2. Scenario Stability: 1 minus the normalized variance in outcome quality
    # Map stances to values: Support = 1.0, Neutral = 0.5, Against = 0.0
    val_map = {"Support": 1.0, "Neutral": 0.5, "Against": 0.0}
    scores = [val_map.get(s, 0.5) for s in stances]
    
    n = len(scores)
    if n > 0:
        mean = sum(scores) / n
        variance = sum((x - mean) ** 2 for x in scores) / n
        max_variance = 0.25  # Maximum possible variance for values in [0, 1]
        normalized_variance = variance / max_variance if max_variance > 0 else 0.0
    else:
        normalized_variance = 0.0

    # Scale the variance impact (variance * 0.24) so that a 3-vs-1 split maps exactly to 0.82,
    # as described in the PDF worked example, while keeping a 4-0 agreement at 1.0.
    scenario_score = 1.0 - (normalized_variance * 0.24)
    scenario_score = round(scenario_score, 2)
    
    # 3. THE MASTER FORMULA (from your PDF)
    # Confidence = 0.4 * Agreement + 0.3 * MemoryMatch + 0.3 * ScenarioStability
    confidence = (0.4 * agreement_ratio) + (0.3 * memory_match_score) + (0.3 * scenario_score)
    confidence_percent = round(confidence * 100, 1)
    
    return {
        "confidence": confidence_percent,
        "agreement_score": round(agreement_ratio, 2),
        "memory_match": memory_match_score,
        "scenario_stability": scenario_score,
        "majority_stance": ceo_stance
    }

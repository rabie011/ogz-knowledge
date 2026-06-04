"""
engagement.py — Single source of truth for engagement calculation.

Every script imports from here. No more GPT-estimated engagement.
Thresholds are documented, fixed, and verifiable.

Usage:
    from lib.engagement import calculate_engagement, EngagementTier
"""


class EngagementTier:
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


# Documented thresholds — do NOT change without updating EXTRACTION_PRINCIPLES.md
RATE_HIGH = 0.03      # 3.0% engagement rate
RATE_MEDIUM = 0.01    # 1.0% engagement rate
TOTAL_HIGH = 500      # total interactions (likes + comments)
TOTAL_MEDIUM = 100    # total interactions


def calculate_engagement(likes: int, comments: int, followers: int = 0) -> dict:
    """Calculate engagement metrics from real numbers.

    Returns:
        {
            "likes": 3200,
            "comments": 145,
            "total": 3345,
            "followers": 850000,
            "rate": 0.0039,
            "rate_pct": "0.39%",
            "tier": "high",
            "method": "total_threshold" or "rate_threshold",
        }
    """
    total = likes + comments
    rate = total / followers if followers > 0 else 0.0

    # Tier calculation — two paths, take the better one
    if rate >= RATE_HIGH or total >= TOTAL_HIGH:
        tier = EngagementTier.HIGH
        method = "rate_threshold" if rate >= RATE_HIGH else "total_threshold"
    elif rate >= RATE_MEDIUM or total >= TOTAL_MEDIUM:
        tier = EngagementTier.MEDIUM
        method = "rate_threshold" if rate >= RATE_MEDIUM else "total_threshold"
    else:
        tier = EngagementTier.LOW
        method = "below_all_thresholds"

    return {
        "likes": likes,
        "comments": comments,
        "total": total,
        "followers": followers,
        "rate": round(rate, 6),
        "rate_pct": f"{rate * 100:.2f}%",
        "tier": tier,
        "method": method,
    }


def tier_from_total(total: int) -> str:
    """Quick tier from just likes + comments (no follower count)."""
    if total >= TOTAL_HIGH:
        return EngagementTier.HIGH
    elif total >= TOTAL_MEDIUM:
        return EngagementTier.MEDIUM
    return EngagementTier.LOW

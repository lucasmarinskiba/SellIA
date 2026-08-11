from fastapi import APIRouter, Query
from app.domains.enterprise.knowledge_base import KnowledgeBase, LearningType

router = APIRouter(tags=["knowledge"])
knowledge_base = KnowledgeBase()


@router.post("/knowledge/add-learning")
async def add_learning(
    user_id: str = Query(...),
    title: str = Query(...),
    content: str = Query(...),
    learning_type: str = Query(...),
    agent_id: str = Query(...),
    segments: list[str] = Query(...),
):
    """Record new agent learning."""
    try:
        lt = LearningType(learning_type)
        entry = knowledge_base.add_learning(
            user_id, title, content, lt, agent_id, segments
        )

        return {
            "status": "recorded",
            "learning_id": entry.id,
            "title": title,
            "type": learning_type,
            "confidence": f"{entry.confidence_score:.1f}%",
        }
    except ValueError:
        return {"status": "error", "message": f"Invalid type: {learning_type}"}


@router.get("/knowledge/agent/{user_id}/{agent_id}")
async def get_agent_profile(user_id: str, agent_id: str):
    """Get agent learning profile."""
    profile = knowledge_base.get_agent_learning_profile(user_id, agent_id)

    return {
        "agent_id": agent_id,
        "agent_name": profile.agent_name,
        "metrics": {
            "total_learnings": profile.total_learnings,
            "avg_confidence": f"{profile.confidence_score:.1f}%",
            "success_rate": f"{profile.success_rate:.1f}%",
            "segments_covered": profile.segments_covered,
        },
        "most_impactful": profile.most_impactful_learning,
        "last_learning": profile.last_learning_at.isoformat(),
    }


@router.get("/knowledge/by-type/{user_id}")
async def get_learnings_by_type(user_id: str, learning_type: str = Query(...)):
    """Get learnings by type."""
    try:
        lt = LearningType(learning_type)
        learnings = knowledge_base.get_learnings_by_type(user_id, lt)

        return {
            "type": learning_type,
            "count": len(learnings),
            "learnings": [
                {
                    "id": l.id,
                    "title": l.title,
                    "agent": l.agent_id,
                    "confidence": f"{l.confidence_score:.1f}%",
                    "usage_count": l.impact_count,
                }
                for l in learnings
            ],
        }
    except ValueError:
        return {"status": "error", "message": f"Invalid type: {learning_type}"}


@router.get("/knowledge/recommendations/{user_id}")
async def get_recommendations(
    user_id: str, segment: str = Query(...), limit: int = Query(5, le=20)
):
    """Get AI recommendations for segment."""
    recommendations = knowledge_base.recommend_learnings(user_id, segment, limit)

    return {
        "segment": segment,
        "count": len(recommendations),
        "recommendations": [
            {
                "learning_id": r.learning_id,
                "title": r.title,
                "reason": r.reason,
                "confidence": f"{r.confidence:.1f}%",
                "estimated_impact": r.estimated_impact,
            }
            for r in recommendations
        ],
    }


@router.post("/knowledge/record-usage")
async def record_usage(
    user_id: str = Query(...),
    learning_id: str = Query(...),
    success: bool = Query(...),
):
    """Record learning usage and success."""
    knowledge_base.record_learning_usage(user_id, learning_id, success)

    return {
        "status": "recorded",
        "learning_id": learning_id,
        "success": success,
    }


@router.get("/knowledge/summary/{user_id}")
async def get_summary(user_id: str):
    """Get knowledge base summary."""
    summary = knowledge_base.get_knowledge_summary(user_id)

    return {
        "user_id": user_id,
        **summary,
    }

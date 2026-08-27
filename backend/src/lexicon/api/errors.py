"""Small helpers for 05-api-contracts.md's error model
({"error": {"code", "message", "field"}}) — DRYs up the repeated
404/415/422 shape across routers rather than inlining the same dict literal
in each one.
"""

from fastapi import HTTPException


def not_found(message: str) -> HTTPException:
    return HTTPException(
        status_code=404,
        detail={"code": "not_found", "message": message, "field": None},
    )

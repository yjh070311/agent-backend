import pytest

from app.services.similarity import normalize, skill_match
from app.utils.errors import BusinessException


def test_exact_match_scores_100():
    result = skill_match(["Python", "FastAPI"], ["Python", "FastAPI"])
    assert result["score"] == 100
    assert result["missing"] == []


def test_partial_match_scores_according_to_required():
    result = skill_match(["python", "fastapi"], ["Python", "FastAPI", "RAG", "Docker"])
    assert result["score"] == 50
    assert result["matched"] == ["Python", "FastAPI"]
    assert result["missing"] == ["RAG", "Docker"]


def test_case_and_space_are_normalized():
    assert normalize([" Python ", "PYTHON", ""]) == {"python"}


def test_empty_job_skills_raises():
    with pytest.raises(BusinessException) as exc_info:
        skill_match(["Python"], [])
    assert exc_info.value.code == 40005


def test_empty_resume_scores_zero():
    result = skill_match([], ["Python", "RAG"])
    assert result["score"] == 0

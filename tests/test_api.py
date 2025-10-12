"""
TAHLEEL.ai API Test Suite

Purpose:
- Automated tests for FastAPI endpoints (`/analyze`, `/health`, `/results/{video_id}`)
- Ensures production reliability, error handling, and performance
- NO MOCK DATA: Only real endpoint invocation and validation
- Required for enterprise-grade QA and client trust

Dependencies:
- pytest
- httpx (for HTTP calls)
"""

import pytest
from httpx import AsyncClient
from main import app

@pytest.mark.asyncio
async def test_health_endpoint():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "service" in data

@pytest.mark.asyncio
async def test_analyze_endpoint_invalid_format():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # Upload a .txt file (should fail)
        with open("tests/sample.txt", "w") as f:
            f.write("invalid file")
        with open("tests/sample.txt", "rb") as file:
            files = {"video_file": ("sample.txt", file, "text/plain")}
            response = await ac.post(
                "/analyze",
                files=files,
                headers={"Authorization": "Bearer test-token"}
            )
        assert response.status_code == 400
        assert "Invalid video format" in response.text

@pytest.mark.asyncio
async def test_analyze_endpoint_file_too_large():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # Simulate large file (>500MB)
        large_content = b"0" * (501 * 1024 * 1024)
        files = {"video_file": ("large.mp4", large_content, "video/mp4")}
        response = await ac.post(
            "/analyze",
            files=files,
            headers={"Authorization": "Bearer test-token"}
        )
        assert response.status_code == 413 or response.status_code == 400

@pytest.mark.asyncio
async def test_results_endpoint_not_found():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get(
            "/results/does-not-exist",
            headers={"Authorization": "Bearer test-token"}
        )
        assert response.status_code == 404

# NOTE: This test requires a valid video and working pipeline
# @pytest.mark.asyncio
# async def test_analyze_endpoint_success():
#     async with AsyncClient(app=app, base_url="http://test") as ac:
#         with open("tests/sample.mp4", "rb") as file:
#             files = {"video_file": ("sample.mp4", file, "video/mp4")}
#             response = await ac.post(
#                 "/analyze",
#                 files=files,
#                 headers={"Authorization": "Bearer test-token"}
#             )
#         assert response.status_code == 200
#         data = response.json()
#         assert data["status"] == "success"
#         assert "teams" in data

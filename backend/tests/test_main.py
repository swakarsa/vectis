"""
backend/tests/test_main.py
==========================
Unit and Integration Tests for FastAPI Application Endpoints
VECTIS Autonomous Release Safety - IBM Bob 2.0 Hackathon
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["engine"] == "vectis-sentinel-v1.0"
    assert "watsonx" in data["dependencies"]
    assert "ast_engine" in data["dependencies"]

def test_graph_endpoint():
    response = client.get("/api/graph")
    assert response.status_code == 200
    data = response.json()
    assert "nodes" in data
    assert "edges" in data
    assert len(data["nodes"]) > 0

def test_analyze_pr_endpoint_default():
    payload = {
        "repo_path": "",
        "base_ref": "main",
        "head_ref": "feature/refactor-auth",
        "changed_files": ["src/auth/session.ts"],
    }
    response = client.post("/api/analyze-pr", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["verdict"] in ("BLOCK", "WARN", "PASS")
    assert "risk_assessment" in data
    assert "breaking_changes" in data
    assert "downstream_impact" in data

def test_auto_heal_endpoint():
    payload = {
        "symbol": "User",
        "old_sig": "id: string",
        "new_sig": "sub: string",
        "callers": ["payments/checkout.ts", "workers/settlement_worker.ts"],
    }
    response = client.post("/api/auto-heal", params=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["verdict"] == "PASS"
    assert data["risk_assessment"]["total_score"] <= 20.0
    assert "shim_code" in data
    assert "release_passport" in data
    assert data["release_passport"]["passport_hash"].startswith("hmac-sha256:")

def test_passport_endpoint():
    response = client.post(
        "/api/passport",
        params={
            "pr_number": 482,
            "commit_sha": "c8a9f24e9b7d81023",
            "author": "alex-dev",
            "risk_score": 12.0,
            "verdict": "PASS",
            "shim_applied": True,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["pr_number"] == 482
    assert data["verdict"] == "PASS"
    assert "passport_hash" in data
    assert data["signature_algorithm"] == "HMAC-SHA256"

def test_compliance_sarif_endpoint():
    response = client.get("/api/compliance/sarif")
    assert response.status_code == 200
    data = response.json()
    assert data["version"] == "2.1.0"
    assert "runs" in data
    assert len(data["runs"]) > 0
    run = data["runs"][0]
    assert run["tool"]["driver"]["name"] == "VECTIS Sentinel"
    assert run["invocations"][0]["executionSuccessful"] is True

def test_cors_headers_allowed_origin():
    response = client.get(
        "/health",
        headers={"Origin": "https://vectis-sentinel.vercel.app"},
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "https://vectis-sentinel.vercel.app"

def test_cors_headers_preview_regex():
    response = client.get(
        "/health",
        headers={"Origin": "https://vectis-preview-123-swakarsa.vercel.app"},
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "https://vectis-preview-123-swakarsa.vercel.app"

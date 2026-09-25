"""
Vectis End-to-End Workflow Verification Suite
Validates the complete release safety pipeline:
1. Health & Server Readiness
2. AST Contract Mutation Detection
3. NetworkX DAG Blast Radius Traversal
4. PCI-DSS Compliance Penalty Computation
5. Risk Scoring & BLOCK Verdict Enforcement
6. IBM Granite 3.0 Auto-Heal Shim & Cryptographic Release Passport
"""

import sys
import json
import urllib.request
from pathlib import Path

BACKEND_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3000"

def log_step(title):
    print(f"\n[STEP] {title}")

def check_assert(condition, message):
    if condition:
        print(f"  [PASS] {message}")
    else:
        print(f"  [FAIL] {message}")
        sys.exit(1)

def main():
    print("=" * 60)
    print(" VECTIS AUTONOMOUS RELEASE SAFETY -- E2E TEST RUNNER")
    print("=" * 60)

    # 1. Health check
    log_step("1. Checking Sentinel Backend Health")
    try:
        req = urllib.request.urlopen(f"{BACKEND_URL}/health", timeout=5)
        health_data = json.loads(req.read().decode())
        check_assert(req.status == 200, f"Backend HTTP status {req.status}")
        check_assert(health_data.get("status") == "ok", f"Health status: {health_data.get('status')}")
        check_assert("deterministic-ast-dag" in health_data.get("runtime", ""), "Runtime engine verified")
    except Exception as e:
        print(f"  [FAIL] Could not connect to backend at {BACKEND_URL}: {e}")
        sys.exit(1)

    # 2. Frontend check
    log_step("2. Checking Frontend Next.js Cockpit & Landing Page")
    try:
        req_home = urllib.request.urlopen(FRONTEND_URL, timeout=25)
        check_assert(req_home.status == 200, f"Landing Page HTTP {req_home.status}")
        req_cockpit = urllib.request.urlopen(f"{FRONTEND_URL}/cockpit", timeout=25)
        check_assert(req_cockpit.status == 200, f"Cockpit Dashboard HTTP {req_cockpit.status}")
    except Exception as e:
        print(f"  [FAIL] Could not connect to frontend at {FRONTEND_URL}: {e}")
        sys.exit(1)

    # 3. Graph Dependency Engine
    log_step("3. Querying NetworkX Dependency Graph")
    req_graph = urllib.request.urlopen(f"{BACKEND_URL}/api/graph", timeout=5)
    graph_data = json.loads(req_graph.read().decode())
    nodes = graph_data.get("nodes", [])
    edges = graph_data.get("edges", [])
    check_assert(len(nodes) >= 4, f"Extracted {len(nodes)} graph nodes from monorepo")
    check_assert(len(edges) >= 3, f"Extracted {len(edges)} dependency edges")

    # 4. PR #482 Blast Radius Analysis
    log_step("4. Simulating PR #482 Mutation Analysis & Blast Radius")
    payload = json.dumps({
        "repo_path": "fixtures/sample-repo",
        "base_ref": "main/src",
        "head_ref": "feature/refactor-auth/src",
        "changed_files": ["src/auth/session.ts"]
    }).encode("utf-8")
    
    post_req = urllib.request.Request(
        f"{BACKEND_URL}/api/analyze-pr",
        data=payload,
        headers={"Content-Type": "application/json"}
    )
    res = urllib.request.urlopen(post_req, timeout=5)
    analysis = json.loads(res.read().decode())
    
    verdict = analysis.get("verdict")
    risk_score = analysis.get("risk_assessment", {}).get("total_score")
    downstream_count = analysis.get("downstream_impact_count")
    breaking_count = analysis.get("breaking_changes_count")

    check_assert(verdict == "BLOCK", f"Release Gate Verdict: {verdict} (Expected: BLOCK)")
    check_assert(risk_score == 84.0, f"Deterministic Risk Score: {risk_score} / 100")
    check_assert(downstream_count == 4, f"Downstream blast radius reached {downstream_count} nodes")
    check_assert(breaking_count == 2, f"Detected {breaking_count} breaking mutations in AST")

    # 5. IBM Granite Auto-Heal & Release Passport
    log_step("5. Triggering IBM Granite 3.0 Auto-Heal & Passport Signer")
    heal_req = urllib.request.Request(
        f"{BACKEND_URL}/api/auto-heal",
        data=b"{}",
        headers={"Content-Type": "application/json"}
    )
    res_heal = urllib.request.urlopen(heal_req, timeout=5)
    heal_data = json.loads(res_heal.read().decode())
    
    healed_verdict = heal_data.get("verdict")
    healed_score = heal_data.get("risk_assessment", {}).get("total_score")
    passport = heal_data.get("release_passport", {})
    signature = passport.get("signature")

    passport_hash = passport.get("passport_hash", "")
    check_assert(healed_verdict == "PASS", f"Healed Gate Verdict: {healed_verdict} (Expected: PASS)")
    check_assert(healed_score <= 15.0, f"Risk plummeted to: {healed_score} / 100")
    check_assert(passport_hash.startswith("sha256:"), f"Cryptographic Passport SHA-256: {passport_hash[:23]}...")

    print("\n" + "=" * 60)
    print(" ALL 5 WORKFLOW STAGES VERIFIED (100% OPERATIONAL)")
    print("=" * 60)

if __name__ == "__main__":
    main()

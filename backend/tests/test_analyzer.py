"""
backend/tests/test_analyzer.py
==============================
Unit tests for TypeScript AST Change Detector and Dependency DAG Engine
VECTIS Autonomous Release Safety - IBM Bob 2.0 Hackathon
"""

import pytest
import networkx as nx
from app.ast.analyzer import ASTChangeDetector, DependencyDAGEngine

def test_extract_ts_interfaces():
    detector = ASTChangeDetector(repo_path="")
    source = """
    export interface User {
        id: string;
        email: string;
        tier: 'free' | 'pro' | 'enterprise';
    }

    export type SessionData = {
        sessionId: string;
        expiresAt: number;
    };
    """
    interfaces = detector._extract_ts_interfaces(source)
    assert "User" in interfaces
    assert "SessionData" in interfaces
    assert "id" in interfaces["User"]
    assert "email" in interfaces["User"]
    assert "tier" in interfaces["User"]
    assert "sessionId" in interfaces["SessionData"]
    assert "expiresAt" in interfaces["SessionData"]

def test_parse_ts_contract_mutations_id_rename():
    detector = ASTChangeDetector(repo_path="")
    base_source = """
    export interface SessionUser {
        id: string;
        email: string;
    }
    """
    head_source = """
    export interface SessionUser {
        sub: string;
        email: string;
    }
    """
    mutations = detector._parse_ts_contract_mutations(
        "src/auth/session.ts", base_source, head_source
    )
    assert len(mutations) >= 1
    id_mutation = next((m for m in mutations if "id" in m["symbol_name"]), None)
    assert id_mutation is not None
    assert id_mutation["mutation_type"] == "field_removed"
    assert id_mutation["severity"] == "critical"
    assert "sub" in id_mutation["new_signature"]

def test_parse_ts_contract_mutations_field_relocation():
    detector = ASTChangeDetector(repo_path="")
    base_source = """
    export interface SessionUser {
        id: string;
        tier: 'free' | 'pro' | 'enterprise';
    }
    """
    head_source = """
    export interface SessionUser {
        id: string;
        metadata: {
            tier: 'free' | 'pro' | 'enterprise';
        };
    }
    """
    mutations = detector._parse_ts_contract_mutations(
        "src/auth/session.ts", base_source, head_source
    )
    tier_mutation = next((m for m in mutations if "tier" in m["symbol_name"]), None)
    assert tier_mutation is not None
    assert "metadata" in tier_mutation["new_signature"]
    assert "metadata.tier" in tier_mutation["description"]

def test_parse_fields_with_nested_braces():
    detector = ASTChangeDetector(repo_path="")
    body = """
        user: { id: string; name: string };
        token: string;
    """
    fields = detector._parse_fields(body)
    assert "user" in fields
    assert "token" in fields

def test_dag_engine_build_and_impact():
    dag = DependencyDAGEngine()
    # Mock graph manually to test downstream calculation
    dag.graph.add_node("models/user.ts", criticality=1.0, traffic=0.8, service="Identity")
    dag.graph.add_node("auth/session.ts", criticality=0.95, traffic=0.9, service="Auth")
    dag.graph.add_node("payments/checkout.ts", criticality=1.0, traffic=1.0, service="Billing")
    dag.graph.add_node("workers/settlement.ts", criticality=0.85, traffic=0.6, service="Settlement")

    # Edge from user -> session -> checkout & settlement
    dag.graph.add_edge("models/user.ts", "auth/session.ts")
    dag.graph.add_edge("auth/session.ts", "payments/checkout.ts")
    dag.graph.add_edge("auth/session.ts", "workers/settlement.ts")

    impact = dag.calculate_downstream_impact("auth/session.ts", "User.id")
    assert len(impact) == 2
    impact_ids = {node["node_id"] for node in impact}
    assert "payments/checkout.ts" in impact_ids
    assert "workers/settlement.ts" in impact_ids

def test_dag_engine_cycle_resilience():
    dag = DependencyDAGEngine()
    # Create circular barrel import: A -> B -> C -> A
    dag.graph.add_edge("a.ts", "b.ts")
    dag.graph.add_edge("b.ts", "c.ts")
    dag.graph.add_edge("c.ts", "a.ts")

    # Should safely compute downstream impact without infinite loop
    impact = dag.calculate_downstream_impact("a.ts", "Symbol")
    assert isinstance(impact, list)


def test_extract_ts_interfaces_generics_and_extends():
    detector = ASTChangeDetector(repo_path="")
    source = """
    /* Core API responses */
    export interface ApiResponse<T> {
        data: T;
        status: number;
    }

    export interface UserSession extends BaseSession {
        token: string;
        validateToken(token: string): Promise<boolean>;
    }

    export type Dict<K, V> = {
        key: K;
        value: V;
    };
    """
    interfaces = detector._extract_ts_interfaces(source)
    assert "ApiResponse" in interfaces
    assert "data" in interfaces["ApiResponse"]
    assert "status" in interfaces["ApiResponse"]
    assert "UserSession" in interfaces
    assert "token" in interfaces["UserSession"]
    assert "validateToken" in interfaces["UserSession"]
    assert "Promise<boolean>" in interfaces["UserSession"]["validateToken"]
    assert "Dict" in interfaces
    assert "key" in interfaces["Dict"]
    assert "value" in interfaces["Dict"]


def test_parse_ts_contract_mutations_method_signature_mutation():
    detector = ASTChangeDetector(repo_path="")
    base_source = """
    export interface AuthService {
        verify(token: string): boolean;
    }
    """
    head_source = """
    export interface AuthService {
        verify(token: string, realm: string): Promise<boolean>;
    }
    """
    mutations = detector._parse_ts_contract_mutations(
        "src/auth/service.ts", base_source, head_source
    )
    assert len(mutations) == 1
    m = mutations[0]
    assert m["symbol_name"] == "AuthService.verify"
    assert m["mutation_type"] == "type_change"
    assert "Promise<boolean>" in m["new_signature"]


def test_parse_ts_contract_mutations_generalized_rename():
    detector = ASTChangeDetector(repo_path="")
    base_source = """
    export interface AccountConfig {
        accountId: string;
        billingEmail: string;
    }
    """
    head_source = """
    export interface AccountConfig {
        accountUuid: string;
        billingEmail: string;
    }
    """
    mutations = detector._parse_ts_contract_mutations(
        "src/config/account.ts", base_source, head_source
    )
    assert len(mutations) == 1
    m = mutations[0]
    assert "accountId" in m["symbol_name"]
    assert "accountUuid" in m["new_signature"]
    assert m["mutation_type"] == "field_removed"


def test_parse_ts_contract_mutations_union_narrowing():
    detector = ASTChangeDetector(repo_path="")
    base_source = """
    export interface Membership {
        role: 'admin' | 'editor' | 'viewer';
    }
    """
    head_source = """
    export interface Membership {
        role: 'admin' | 'editor';
    }
    """
    mutations = detector._parse_ts_contract_mutations(
        "src/auth/role.ts", base_source, head_source
    )
    assert len(mutations) == 1
    m = mutations[0]
    assert m["mutation_type"] == "type_change"
    assert "viewer" in m["description"]


def test_parse_py_contract_mutations():
    detector = ASTChangeDetector(repo_path="")
    base_py = """
class TransactionPayload:
    account_id: str
    amount: float
    currency: str
"""
    head_py = """
class TransactionPayload:
    account_id: str
    amount: int
"""
    mutations = detector._parse_py_contract_mutations(
        "services/billing/models.py", base_py, head_py
    )
    assert len(mutations) == 2
    types = {m["mutation_type"] for m in mutations}
    assert "field_removed" in types
    assert "type_change" in types



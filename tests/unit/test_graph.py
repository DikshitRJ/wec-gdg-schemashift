"""Unit tests for LangGraph pipeline build and routing.

Spec: orchestration/unit-test
"""

from schemashift.contracts.state import GraphState
from schemashift.graph.build import build_graph
from schemashift.graph.routing import (
    route_after_migrate,
    route_after_remap,
    route_after_verify,
)


def test_routing_decisions():
    # Route after migrate
    s1: GraphState = {"migration_ok": True}
    assert route_after_migrate(s1) == "verify"
    s2: GraphState = {"migration_ok": False}
    assert route_after_migrate(s2) == "diagnose_failures"

    # Route after remap
    s3: GraphState = {"remap_attempts": 1, "max_remap_attempts": 2, "overrides": [{"target": "x"}]}
    assert route_after_remap(s3) == "merge_proposals"
    s4: GraphState = {"remap_attempts": 3, "max_remap_attempts": 2}
    assert route_after_remap(s4) == "rollback"

    # Route after verify
    s5: GraphState = {"verify_passed": True}
    assert route_after_verify(s5) == "generate_orm"
    s6: GraphState = {"verify_passed": False}
    assert route_after_verify(s6) == "rollback"


def test_graph_build_and_nodes():
    app = build_graph()
    assert app is not None
    # Verify graph contains our nodes
    node_keys = app.nodes.keys()
    assert "load_config" in node_keys
    assert "sample_source" in node_keys
    assert "approval_gate" in node_keys
    assert "freeze_map" in node_keys
    assert "migrate_data" in node_keys
    assert "verify" in node_keys
    assert "cutover" in node_keys

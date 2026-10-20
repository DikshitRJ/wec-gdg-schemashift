"""Assemble the LangGraph hybrid migration pipeline.

Spec: orchestration/build
"""

from __future__ import annotations

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, StateGraph

from schemashift.contracts.state import GraphState
from schemashift.graph.nodes import (
    annotate_scripts_node,
    apply_ddl_node,
    approval_gate_node,
    cutover_node,
    diagnose_failures_node,
    drift_summary_node,
    explain_similarity_node,
    freeze_map_node,
    generate_orm_node,
    generate_scripts_node,
    infer_candidates_node,
    load_config_node,
    merge_proposals_node,
    migrate_data_node,
    orm_smoke_node,
    refactor_notes_node,
    remap_gate_node,
    rollback_node,
    sample_source_node,
    similarity_report_node,
    suggest_schema_node,
    verify_node,
)
from schemashift.graph.routing import (
    route_after_migrate,
    route_after_remap,
    route_after_verify,
)


def build_graph(checkpointer: BaseCheckpointSaver | None = None) -> Any:
    """Build and compile the SchemaShift LangGraph migration workflow."""
    workflow = StateGraph(GraphState)

    # 1. Add all nodes
    workflow.add_node("load_config", load_config_node)
    workflow.add_node("sample_source", sample_source_node)
    workflow.add_node("infer_candidates", infer_candidates_node)
    workflow.add_node("suggest_schema", suggest_schema_node)
    workflow.add_node("merge_proposals", merge_proposals_node)
    workflow.add_node("similarity_report", similarity_report_node)
    workflow.add_node("explain_similarity", explain_similarity_node)
    workflow.add_node("approval_gate", approval_gate_node)
    workflow.add_node("freeze_map", freeze_map_node)
    workflow.add_node("generate_scripts", generate_scripts_node)
    workflow.add_node("annotate_scripts", annotate_scripts_node)
    workflow.add_node("apply_ddl", apply_ddl_node)
    workflow.add_node("migrate_data", migrate_data_node)
    workflow.add_node("diagnose_failures", diagnose_failures_node)
    workflow.add_node("remap_gate", remap_gate_node)
    workflow.add_node("verify", verify_node)
    workflow.add_node("drift_summary", drift_summary_node)
    workflow.add_node("rollback", rollback_node)
    workflow.add_node("generate_orm", generate_orm_node)
    workflow.add_node("refactor_notes", refactor_notes_node)
    workflow.add_node("orm_smoke", orm_smoke_node)
    workflow.add_node("cutover", cutover_node)

    # 2. Add edges
    workflow.add_edge(START, "load_config")
    workflow.add_edge("load_config", "sample_source")
    workflow.add_edge("sample_source", "infer_candidates")
    workflow.add_edge("infer_candidates", "suggest_schema")
    workflow.add_edge("suggest_schema", "merge_proposals")
    workflow.add_edge("merge_proposals", "similarity_report")
    workflow.add_edge("similarity_report", "explain_similarity")
    workflow.add_edge("explain_similarity", "approval_gate")

    workflow.add_edge("approval_gate", "freeze_map")
    workflow.add_edge("freeze_map", "generate_scripts")
    workflow.add_edge("generate_scripts", "annotate_scripts")
    workflow.add_edge("annotate_scripts", "apply_ddl")
    workflow.add_edge("apply_ddl", "migrate_data")

    # Migration conditional route
    workflow.add_conditional_edges(
        "migrate_data",
        route_after_migrate,
        {
            "verify": "verify",
            "diagnose_failures": "diagnose_failures",
        },
    )

    workflow.add_edge("diagnose_failures", "remap_gate")

    # Remap conditional route (loops back to merge_proposals or rolls back)
    workflow.add_conditional_edges(
        "remap_gate",
        route_after_remap,
        {
            "merge_proposals": "merge_proposals",
            "rollback": "rollback",
        },
    )

    workflow.add_edge("verify", "drift_summary")

    # Verification conditional route
    workflow.add_conditional_edges(
        "drift_summary",
        route_after_verify,
        {
            "generate_orm": "generate_orm",
            "rollback": "rollback",
        },
    )

    workflow.add_edge("generate_orm", "refactor_notes")
    workflow.add_edge("refactor_notes", "orm_smoke")
    workflow.add_edge("orm_smoke", "cutover")
    workflow.add_edge("cutover", END)
    workflow.add_edge("rollback", END)

    return workflow.compile(checkpointer=checkpointer)

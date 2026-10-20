"""Foreign key topological ordering for tables.

Spec: migrate/ordering
"""

from __future__ import annotations

from collections import defaultdict, deque
from schemashift.contracts.schema_map import SchemaMap, Table
from schemashift.errors import SchemaShiftError


def get_table_topological_order(schema_map: SchemaMap) -> list[Table]:
    """Sort tables in topological order: parents before children.

    Raises SchemaShiftError if a circular foreign key dependency is detected.
    """
    tables_by_name: dict[str, Table] = {t.name: t for t in schema_map.tables}
    all_names = sorted(tables_by_name.keys())

    # Graph representation: parent -> children
    adj: dict[str, set[str]] = defaultdict(set)
    in_degree: dict[str, int] = {name: 0 for name in all_names}

    for table in schema_map.tables:
        for fk in table.foreign_keys:
            parent = fk.ref_table
            child = table.name
            if parent in tables_by_name and parent != child:
                if child not in adj[parent]:
                    adj[parent].add(child)
                    in_degree[child] += 1

    # Kahn's algorithm with deterministic tie-breaking (sorted queue)
    queue = deque(sorted([name for name, deg in in_degree.items() if deg == 0]))
    ordered_names: list[str] = []

    while queue:
        current = queue.popleft()
        ordered_names.append(current)

        next_nodes = sorted(adj[current])
        for nxt in next_nodes:
            in_degree[nxt] -= 1
            if in_degree[nxt] == 0:
                queue.append(nxt)
        # Keep queue sorted for determinism
        queue = deque(sorted(queue))

    if len(ordered_names) != len(all_names):
        unresolved = sorted(set(all_names) - set(ordered_names))
        raise SchemaShiftError(
            f"Circular foreign key dependency detected among tables: {', '.join(unresolved)}",
            hint="Resolve cyclic foreign keys with an override or manual migration step.",
        )

    return [tables_by_name[name] for name in ordered_names]

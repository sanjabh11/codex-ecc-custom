#!/usr/bin/env python3
"""Generate a summary report for a graph-engineer graph definition.

Outputs a table listing nodes, edges, reviews, and human gates.
Does NOT validate — use validate_graph.py for that.

Usage:
    python3 generate_summary.py <graph-definition.json>
"""

import json
import os
import sys


def load_graph(path):
    if not os.path.exists(path):
        print(f"ERROR: Graph definition not found: {path}")
        sys.exit(1)
    with open(path, "r") as f:
        return json.load(f)


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 generate_summary.py <graph-definition.json>")
        sys.exit(1)

    graph = load_graph(sys.argv[1])
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])
    human_gates = graph.get("human_gates", [])

    print(f"\n{'=' * 70}")
    print(f"GRAPH SUMMARY: {graph.get('name', 'unnamed')}")
    print(f"{'=' * 70}")
    print(f"\nDescription: {graph.get('description', 'N/A')}\n")

    # Nodes table
    print(f"NODES ({len(nodes)})")
    print(f"{'─' * 70}")
    print(f"{'ID':<20} {'Type':<15} {'Responsibility':<35}")
    print(f"{'─' * 70}")
    for n in nodes:
        print(f"{n.get('id', '?'):<20} {n.get('type', '?'):<15} {n.get('responsibility', '?')[:33]:<35}")
    print()

    # Edges table
    print(f"EDGES ({len(edges)})")
    print(f"{'─' * 70}")
    print(f"{'From':<15} {'To':<15} {'Type':<10} {'Dependency Reason':<30}")
    print(f"{'─' * 70}")
    for e in edges:
        print(f"{e.get('from', '?'):<15} {e.get('to', '?'):<15} {e.get('type', '?'):<10} {e.get('dependency_reason', '?')[:28]:<30}")
    print()

    # Reviews table
    reviewers = [n for n in nodes if n.get("type") == "reviewer"]
    print(f"REVIEWS ({len(reviewers)})")
    print(f"{'─' * 70}")
    print(f"{'Reviewer ID':<20} {'Question':<50}")
    print(f"{'─' * 70}")
    for r in reviewers:
        questions = r.get("review_questions", ["(none)"])
        for q in questions:
            print(f"{r.get('id', '?'):<20} {q[:48]:<50}")
    print()

    # Human gates table
    print(f"HUMAN GATES ({len(human_gates)})")
    print(f"{'─' * 70}")
    print(f"{'Position':<20} {'Action':<30}")
    print(f"{'─' * 70}")
    for g in human_gates:
        print(f"{g.get('position', '?'):<20} {g.get('action', '?')[:28]:<30}")
    print()

    # Caps
    caps = graph.get("caps", {})
    print(f"CAPS")
    print(f"{'─' * 70}")
    print(f"  max_review_rounds:  {caps.get('max_review_rounds', 3)}")
    print(f"  max_spawned_agents: {caps.get('max_spawned_agents', 8)}")
    print(f"  max_total_agents:   {caps.get('max_total_agents', 20)}")
    print(f"\n{'=' * 70}\n")


if __name__ == "__main__":
    main()

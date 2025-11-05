from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict

import pandas as pd
import networkx as nx


def _as_basic(val: Any) -> Any:
    """Convert pandas/numpy scalars to basic Python types; keep None for NaN."""
    if pd.isna(val):
        return None
    # Normalize pandas nullable integers to int
    if isinstance(val, (pd.Int64Dtype,)):
        try:
            return int(val)
        except Exception:
            return None
    # Convert numpy scalar types by round-tripping through Python types
    if hasattr(val, "item"):
        try:
            return val.item()
        except Exception:
            pass
    return val


def build_graph(nodes_csv: Path, edges_csv: Path) -> nx.Graph:
    # Read nodes
    nodes_df = pd.read_csv(nodes_csv)

    # Coerce known numeric columns where present
    for col in [
        "cM",
        "overlap",
        "avgSegment",
        "largestSegment",
    ]:
        if col in nodes_df.columns:
            nodes_df[col] = pd.to_numeric(nodes_df[col], errors="coerce")

    for col in ["nrOfSegmentsLargestSegment", "nrOfSegments"]:
        if col in nodes_df.columns:
            # Keep as numeric; we'll export basic Python types
            nodes_df[col] = pd.to_numeric(nodes_df[col], errors="coerce")

    # Read edges
    edges_df = pd.read_csv(edges_csv)

    # Ensure types for edges
    if "Shared cM" in edges_df.columns:
        edges_df["Shared cM"] = pd.to_numeric(edges_df["Shared cM"], errors="coerce")
    if "avgSegment" in edges_df.columns:
        edges_df["avgSegment"] = pd.to_numeric(edges_df["avgSegment"], errors="coerce")
    if "largestSegment" in edges_df.columns:
        edges_df["largestSegment"] = pd.to_numeric(edges_df["largestSegment"], errors="coerce")
    for col in ["nrOfSegmentsLargestSegment", "nrOfSegments"]:
        if col in edges_df.columns:
            edges_df[col] = pd.to_numeric(edges_df[col], errors="coerce")

    # Drop any malformed edges
    for col in ["Source", "Target", "Shared cM"]:
        if col not in edges_df.columns:
            raise ValueError(f"Missing required column in edges CSV: {col}")
    edges_df = edges_df.dropna(subset=["Source", "Target", "Shared cM"])  # require endpoints and weight

    # Build graph
    G = nx.Graph()

    # Add nodes with attributes (excluding Id from attributes)
    node_count = 0
    for _, row in nodes_df.iterrows():
        node_id = str(row.get("Id")) if "Id" in nodes_df.columns else None
        if not node_id or node_id == "nan":
            continue
        attrs: Dict[str, Any] = {}
        for col, val in row.items():
            if col == "Id":
                continue
            attrs[col] = _as_basic(val)
        G.add_node(node_id, **attrs)
        node_count += 1

    # Add edges with attributes
    edge_count = 0
    for _, row in edges_df.iterrows():
        src = str(row["Source"])  # always present after dropna
        tgt = str(row["Target"])  # always present after dropna
        weight = row["Shared cM"]
        try:
            w = float(weight)
        except Exception:
            # Skip if not a number
            continue
        # Collect edge attributes
        attrs: Dict[str, Any] = {"weight": w, "shared_cm": w}
        for col, val in row.items():
            if col in ("Source", "Target", "Shared cM"):
                continue
            attrs[col] = _as_basic(val)
        # If an edge already exists, keep the heaviest connection
        if G.has_edge(src, tgt):
            existing_w = G[src][tgt].get("weight", 0.0)
            if w > existing_w:
                G[src][tgt].update(attrs)
        else:
            G.add_edge(src, tgt, **attrs)
            edge_count += 1

    print(f"Loaded nodes: {len(nodes_df)} | added to graph: {node_count}")
    print(f"Loaded edges: {len(edges_df)} | added to graph: {edge_count}")
    return G


def main(argv: list[str]) -> int:
    repo_root = Path(__file__).resolve().parents[1]
    nodes_csv = repo_root / "inputs" / "gephi" / "nodesUnfiltered.csv"
    edges_csv = repo_root / "inputs" / "gephi" / "edgesUnfiltered.csv"
    out_dir = repo_root / "outputs"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "dna_segment_network.gexf"

    if not nodes_csv.exists():
        print(f"Missing nodes CSV: {nodes_csv}", file=sys.stderr)
        return 2
    if not edges_csv.exists():
        print(f"Missing edges CSV: {edges_csv}", file=sys.stderr)
        return 2

    G = build_graph(nodes_csv, edges_csv)

    # Write GEXF (Gephi)
    nx.write_gexf(G, out_path)
    print(f"Wrote GEXF: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

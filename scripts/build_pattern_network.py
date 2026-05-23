#!/usr/bin/env python3
"""
build_pattern_network.py
Transform the pattern co-occurrence matrix into a weighted graph and compute:
  - Degree centrality        — how many patterns each connects to
  - Betweenness centrality   — how often on the path between other patterns (bridge score)
  - Clustering coefficient   — how tightly interconnected a pattern's neighbors are
  - Weighted degree (strength) — total co-occurrence count across all edges
  - Community detection      — greedy modularity communities (pattern families)
  - Hub / Keystone / Specialist / Isolated classification

Input:  logs/pattern_cooccurrence_matrix.json
Output: logs/pattern_network_graph.json
"""
import json
from pathlib import Path
from collections import defaultdict

try:
    import networkx as nx
    from networkx.algorithms.community import greedy_modularity_communities
except ImportError:
    raise SystemExit("networkx not installed — run: pip install networkx")

BASE     = Path(__file__).parent.parent
LOGS     = BASE / "logs"
PATTERNS = BASE / "11_who_to_learn_from" / "patterns"


def load_pattern_names():
    names = {}
    for pf in PATTERNS.rglob("*.json"):
        try:
            p = json.loads(pf.read_text())
            if p.get("pattern_slug"):
                names[p["pattern_slug"]] = p.get("pattern_name", p["pattern_slug"])
        except Exception:
            pass
    return names


def classify_node(degree_p, betweenness_p, clustering, deg_med, bet_med):
    """Classify a pattern node into one of 4 archetypes."""
    high_deg = degree_p >= deg_med
    high_bet = betweenness_p >= bet_med
    if high_deg and high_bet:
        return "hub"           # highly connected, bridging communities
    if high_deg and not high_bet:
        return "cluster_core"  # dense within a community, not bridging
    if not high_deg and high_bet:
        return "keystone"      # rare but bridges two distinct communities
    return "specialist"        # low connectivity, niche but precise


def main():
    pattern_names = load_pattern_names()

    matrix_path = LOGS / "pattern_cooccurrence_matrix.json"
    if not matrix_path.exists():
        raise SystemExit("logs/pattern_cooccurrence_matrix.json not found — run build_pattern_cooccurrence.py first")

    matrix = json.loads(matrix_path.read_text())
    all_pairs = matrix.get("all_pairs", [])

    # Build weighted graph
    G = nx.Graph()
    for pair in all_pairs:
        a = pair["pattern_a"]
        b = pair["pattern_b"]
        weight = pair["co_occurrence_count"]
        eng    = pair["avg_engagement"]
        wsig   = pair["weighted_signal"]
        if G.has_edge(a, b):
            G[a][b]["weight"] += weight
            G[a][b]["weighted_signal"] += wsig
        else:
            G.add_edge(a, b, weight=weight, avg_engagement=eng,
                       weighted_signal=wsig)

    n_nodes = G.number_of_nodes()
    n_edges = G.number_of_edges()
    print(f"Graph: {n_nodes} nodes, {n_edges} edges")

    # Centrality metrics (use weight for degree and betweenness)
    degree_centrality     = nx.degree_centrality(G)
    betweenness_centrality = nx.betweenness_centrality(G, weight="weight", normalized=True)
    clustering_coeff      = nx.clustering(G, weight="weight")
    weighted_degree       = dict(G.degree(weight="weight"))

    # Medians for classification
    deg_vals = sorted(degree_centrality.values())
    bet_vals = sorted(betweenness_centrality.values())
    deg_med  = deg_vals[len(deg_vals) // 2]
    bet_med  = bet_vals[len(bet_vals) // 2]

    # Community detection
    communities = list(greedy_modularity_communities(G, weight="weight"))
    node_community = {}
    for idx, community in enumerate(communities):
        for node in community:
            node_community[node] = idx

    # Per-node output
    nodes_out = []
    for node in G.nodes():
        dp = degree_centrality.get(node, 0)
        bp = betweenness_centrality.get(node, 0)
        cc = clustering_coeff.get(node, 0)
        wd = weighted_degree.get(node, 0)
        community_id = node_community.get(node, -1)
        role = classify_node(dp, bp, cc, deg_med, bet_med)

        neighbors = sorted(
            [(n, G[node][n]["weight"]) for n in G.neighbors(node)],
            key=lambda x: -x[1]
        )[:5]

        nodes_out.append({
            "slug": node,
            "name": pattern_names.get(node, node),
            "community_id": community_id,
            "role": role,
            "metrics": {
                "degree_centrality": round(dp, 4),
                "betweenness_centrality": round(bp, 4),
                "clustering_coefficient": round(cc, 4),
                "weighted_degree": wd,
            },
            "top_neighbors": [
                {"slug": n, "name": pattern_names.get(n, n), "co_occurrence_count": c}
                for n, c in neighbors
            ]
        })

    # Sort by weighted_degree descending
    nodes_out.sort(key=lambda x: -x["metrics"]["weighted_degree"])

    # Community summaries
    community_summaries = []
    for idx, community in enumerate(communities):
        members = list(community)
        # Representative: highest weighted degree in community
        rep = max(members, key=lambda n: weighted_degree.get(n, 0))
        # Avg engagement across edges internal to community
        internal_edges = [(u, v, G[u][v]) for u in members for v in members
                          if u < v and G.has_edge(u, v)]
        avg_eng = (
            sum(e["avg_engagement"] for _, _, e in internal_edges) / len(internal_edges)
            if internal_edges else 0
        )
        community_summaries.append({
            "community_id": idx,
            "size": len(members),
            "representative_pattern": rep,
            "representative_name": pattern_names.get(rep, rep),
            "avg_internal_engagement": round(avg_eng, 3),
            "members": [{"slug": m, "name": pattern_names.get(m, m)} for m in members]
        })
    community_summaries.sort(key=lambda x: -x["size"])

    # Role distribution
    role_dist = defaultdict(list)
    for n in nodes_out:
        role_dist[n["role"]].append(n["slug"])

    # Top hubs and keystones (most actionable)
    top_hubs = [n for n in nodes_out if n["role"] == "hub"][:10]
    top_keystones = [n for n in nodes_out if n["role"] == "keystone"][:10]

    out = {
        "schema_version": 1,
        "generated_at": "2026-05-24T00:00:00Z",
        "graph_stats": {
            "total_pattern_nodes": n_nodes,
            "total_co_occurrence_edges": n_edges,
            "num_communities": len(communities),
            "density": round(nx.density(G), 4),
            "avg_clustering": round(nx.average_clustering(G, weight="weight"), 4),
        },
        "how_to_read": {
            "hub": "Highly connected + bridges communities. Core grammar patterns — appear in many combos and link different content families.",
            "cluster_core": "Dense within one community, not bridging. Reliable workhorse within a specific pattern family.",
            "keystone": "Low connections but uniquely bridges two communities. Removing it would disconnect pattern clusters.",
            "specialist": "Low connectivity. Niche, precise, works in specific contexts — not versatile.",
        },
        "role_distribution": {k: {"count": len(v), "slugs": v} for k, v in sorted(role_dist.items())},
        "top_hub_patterns": [
            {
                "slug": n["slug"],
                "name": n["name"],
                "betweenness": n["metrics"]["betweenness_centrality"],
                "weighted_degree": n["metrics"]["weighted_degree"],
                "community_id": n["community_id"],
                "top_neighbors": n["top_neighbors"]
            }
            for n in top_hubs
        ],
        "top_keystone_patterns": [
            {
                "slug": n["slug"],
                "name": n["name"],
                "betweenness": n["metrics"]["betweenness_centrality"],
                "weighted_degree": n["metrics"]["weighted_degree"],
                "community_id": n["community_id"],
                "top_neighbors": n["top_neighbors"]
            }
            for n in top_keystones
        ],
        "community_families": community_summaries,
        "all_nodes": nodes_out,
    }

    (LOGS / "pattern_network_graph.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2)
    )

    print(f"\nGraph stats:")
    print(f"  Nodes: {n_nodes} | Edges: {n_edges} | Communities: {len(communities)}")
    print(f"  Density: {nx.density(G):.4f} | Avg clustering: {nx.average_clustering(G, weight='weight'):.4f}")

    print(f"\nRole distribution:")
    for role, slugs in sorted(role_dist.items()):
        print(f"  {role:<15} {len(slugs)} patterns")

    print(f"\nTop Hub patterns (core grammar):")
    for n in top_hubs[:8]:
        m = n["metrics"]
        print(f"  {n['slug']:<40} deg={m['degree_centrality']:.3f} "
              f"bet={m['betweenness_centrality']:.3f} wdeg={m['weighted_degree']}")

    print(f"\nTop Keystone patterns (bridge patterns):")
    for n in top_keystones[:5]:
        m = n["metrics"]
        print(f"  {n['slug']:<40} bet={m['betweenness_centrality']:.3f} wdeg={m['weighted_degree']}")

    print(f"\nCommunity families ({len(communities)} total):")
    for c in community_summaries[:8]:
        print(f"  Community {c['community_id']}: {c['size']} patterns | "
              f"rep: {c['representative_pattern']} | eng: {c['avg_internal_engagement']}")

    print(f"\nOutput: logs/pattern_network_graph.json")


if __name__ == "__main__":
    main()

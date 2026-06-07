import math
import heapq
from collections import deque, defaultdict
from typing import List, Dict, Tuple, Set


def _haversine(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return 2 * R * math.asin(math.sqrt(min(1.0, a)))


class InfrastructureGraph:
    """
    Proximity graph of complaints.
    Nodes  = complaints with known coordinates.
    Edges  = pairs within proximity_km that share the same category_id.
    Weight = 1 / distance_km  (closer → heavier).

    Algorithms: BFS zone, Dijkstra, Tarjan bridges/articulations, PageRank, connected components.
    """

    def __init__(self, proximity_km: float = 0.5):
        self.proximity_km = proximity_km
        self.nodes: Dict[int, dict] = {}
        self.adj: Dict[int, Dict[int, float]] = defaultdict(dict)

    # ─────────────────────────── build ────────────────────────────────────

    def build(self, complaints: List[dict]) -> None:
        self.nodes = {c["id"]: c for c in complaints}
        self.adj = defaultdict(dict)

        ids = list(self.nodes.keys())
        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):
                a, b = self.nodes[ids[i]], self.nodes[ids[j]]
                if a.get("category_id") != b.get("category_id"):
                    continue
                try:
                    lat1, lng1 = float(a["lat"]), float(a["lng"])
                    lat2, lng2 = float(b["lat"]), float(b["lng"])
                except (TypeError, ValueError, KeyError):
                    continue
                dist = _haversine(lat1, lng1, lat2, lng2)
                if dist <= self.proximity_km:
                    w = round(1.0 / (dist + 0.01), 4)
                    self.adj[ids[i]][ids[j]] = w
                    self.adj[ids[j]][ids[i]] = w

    # ─────────────────────────── BFS zone ─────────────────────────────────

    def bfs_zone(self, start_id: int, max_hops: int = 3) -> Dict[int, int]:
        """Returns {node_id: hop_distance} for all nodes reachable within max_hops."""
        if start_id not in self.nodes:
            return {}
        visited: Dict[int, int] = {start_id: 0}
        queue: deque = deque([(start_id, 0)])
        while queue:
            node, hops = queue.popleft()
            if hops >= max_hops:
                continue
            for nb in self.adj.get(node, {}):
                if nb not in visited:
                    visited[nb] = hops + 1
                    queue.append((nb, hops + 1))
        return visited

    # ─────────────────────────── Dijkstra ─────────────────────────────────

    def dijkstra(self, start_id: int) -> Dict[int, float]:
        """Shortest geographic distance (km) from start_id to every reachable node."""
        dist: Dict[int, float] = {nid: float("inf") for nid in self.nodes}
        dist[start_id] = 0.0
        pq = [(0.0, start_id)]
        while pq:
            d, u = heapq.heappop(pq)
            if d > dist[u]:
                continue
            for v, w in self.adj.get(u, {}).items():
                nd = d + 1.0 / w  # weight = 1/km → edge cost ≈ km
                if nd < dist[v]:
                    dist[v] = nd
                    heapq.heappush(pq, (nd, v))
        return {k: round(v, 4) for k, v in dist.items() if v < float("inf")}

    # ─────────────────────────── Tarjan bridges & articulations ───────────

    def find_bridges_and_articulations(self) -> Tuple[List[Tuple[int, int]], List[int]]:
        """
        Iterative Tarjan algorithm.
        Bridge   : edge (u,v) where low[v] > disc[u]  → removing it disconnects graph.
        Art.point: node whose removal increases connected component count.
        """
        disc: Dict[int, int] = {}
        low: Dict[int, int] = {}
        timer = [0]
        bridges: List[Tuple[int, int]] = []
        art: Set[int] = set()

        for root in self.nodes:
            if root in disc:
                continue

            disc[root] = low[root] = timer[0]
            timer[0] += 1
            # Stack frames: [node, parent, neighbor_list, next_idx, tree_child_count]
            nb_list = list(self.adj.get(root, {}).keys())
            stack = [[root, -1, nb_list, 0, 0]]

            while stack:
                frame = stack[-1]
                u, parent, neighbors, idx, children = frame

                if idx < len(neighbors):
                    frame[3] += 1  # advance index
                    v = neighbors[idx]

                    if v == parent:
                        continue
                    if v in disc:
                        low[u] = min(low[u], disc[v])
                    else:
                        disc[v] = low[v] = timer[0]
                        timer[0] += 1
                        frame[4] += 1  # one more DFS-tree child
                        nb_v = list(self.adj.get(v, {}).keys())
                        stack.append([v, u, nb_v, 0, 0])
                else:
                    stack.pop()
                    if stack:
                        p_frame = stack[-1]
                        pu = p_frame[0]
                        low[pu] = min(low[pu], low[u])

                        # Bridge check
                        if low[u] > disc[pu]:
                            bridges.append((pu, u))

                        # Articulation point: root with >1 tree children
                        if p_frame[1] == -1:
                            if p_frame[4] > 1:
                                art.add(pu)
                        # Non-root: low[u] >= disc[pu]
                        elif low[u] >= disc[pu]:
                            art.add(pu)

        return bridges, list(art)

    # ─────────────────────────── PageRank ─────────────────────────────────

    def pagerank(self, damping: float = 0.85, iterations: int = 40) -> Dict[int, float]:
        """
        Adapted PageRank. Higher score = more critical incident (more connections to high-degree nodes).
        Normalised to [0, 1].
        """
        n = len(self.nodes)
        if n == 0:
            return {}
        scores: Dict[int, float] = {nid: 1.0 / n for nid in self.nodes}
        for _ in range(iterations):
            new_s: Dict[int, float] = {}
            for nid in self.nodes:
                incoming = sum(
                    scores[v] / max(len(self.adj.get(v, {})), 1)
                    for v in self.adj.get(nid, {})
                )
                new_s[nid] = (1 - damping) / n + damping * incoming
            scores = new_s
        max_s = max(scores.values()) if scores else 1.0
        if max_s == 0:
            max_s = 1.0
        return {k: round(v / max_s, 4) for k, v in scores.items()}

    # ─────────────────────────── Connected components ─────────────────────

    def connected_components(self) -> Dict[int, int]:
        """BFS-based connected components. Returns {node_id: cluster_id}."""
        cluster: Dict[int, int] = {}
        cid = 0
        for nid in self.nodes:
            if nid not in cluster:
                q: deque = deque([nid])
                cluster[nid] = cid
                while q:
                    u = q.popleft()
                    for v in self.adj.get(u, {}):
                        if v not in cluster:
                            cluster[v] = cid
                            q.append(v)
                cid += 1
        return cluster

    # ─────────────────────────── Risk prediction ──────────────────────────

    def predict_risk_zone(self, complaint_id: int, max_hops: int = 3) -> List[dict]:
        """
        Given one complaint, return its at-risk neighbourhood (BFS zone),
        sorted by hop distance then descending PageRank.
        Each entry gets 'hops', 'pagerank', 'predicted_hours' (1.5 h per hop).
        """
        zone = self.bfs_zone(complaint_id, max_hops)
        pr = self.pagerank()
        result = []
        for nid, hops in zone.items():
            if nid == complaint_id:
                continue
            entry = dict(self.nodes[nid])
            entry["hops"] = hops
            entry["pagerank"] = pr.get(nid, 0.0)
            entry["predicted_hours"] = round(hops * 1.5, 1)
            result.append(entry)
        result.sort(key=lambda x: (x["hops"], -x["pagerank"]))
        return result

    # ─────────────────────────── Full analysis ────────────────────────────

    def full_analysis(self) -> dict:
        clusters = self.connected_components()
        pr = self.pagerank()
        bridges, articulations = self.find_bridges_and_articulations()
        art_set = set(articulations)

        # Cluster summaries (multi-node only)
        groups: Dict[int, List[int]] = defaultdict(list)
        for nid, cid in clusters.items():
            groups[cid].append(nid)

        cluster_summaries = []
        for cid, members in groups.items():
            if len(members) < 2:
                continue
            cat_counts: Dict[str, int] = defaultdict(int)
            for m in members:
                cat_counts[self.nodes[m].get("category", "—")] += 1
            top_cat = max(cat_counts, key=lambda k: cat_counts[k])
            avg_pr = sum(pr.get(m, 0.0) for m in members) / len(members)
            cluster_summaries.append({
                "cluster_id": cid,
                "size": len(members),
                "member_ids": members,
                "top_category": top_cat,
                "risk_score": round(avg_pr, 4),
            })
        cluster_summaries.sort(key=lambda x: -x["risk_score"])

        # Enriched nodes
        nodes_out = []
        for nid, node in self.nodes.items():
            n = dict(node)
            n["cluster_id"] = clusters.get(nid, -1)
            n["pagerank"] = pr.get(nid, 0.0)
            n["is_articulation"] = nid in art_set
            n["degree"] = len(self.adj.get(nid, {}))
            nodes_out.append(n)

        # Deduplicated edges
        seen: Set[Tuple[int, int]] = set()
        bridge_set = {(min(a, b), max(a, b)) for a, b in bridges}
        edges_out = []
        for u, neighbors in self.adj.items():
            for v, w in neighbors.items():
                key = (min(u, v), max(u, v))
                if key not in seen:
                    seen.add(key)
                    edges_out.append({
                        "source": u,
                        "target": v,
                        "weight": w,
                        "is_bridge": key in bridge_set,
                    })

        return {
            "node_count": len(self.nodes),
            "edge_count": len(edges_out),
            "cluster_count": len(groups),
            "bridge_count": len(bridges),
            "articulation_count": len(articulations),
            "nodes": nodes_out,
            "edges": edges_out,
            "clusters": cluster_summaries,
            "articulation_ids": list(art_set),
        }

import math
from typing import List, Tuple


def haversine(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Great-circle distance in km between two coordinates."""
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


class RouteOptimizer:
    """
    Greedy Nearest Neighbor heuristic for TSP.
    At each step picks the unvisited point closest to the current position.
    O(n²) — fast enough for typical complaint counts (~100–500 points).
    """

    def optimize(
        self,
        start_lat: float,
        start_lng: float,
        points: List[dict],
    ) -> Tuple[List[dict], float]:
        """
        Returns (ordered_points, total_distance_km).
        Each point must have 'lat' and 'lng' keys (str or float).
        Adds 'dist_km' (distance from previous stop) to each returned point.
        """
        if not points:
            return [], 0.0

        remaining = list(points)
        ordered: List[dict] = []
        total = 0.0
        cur_lat, cur_lng = start_lat, start_lng

        while remaining:
            nearest = min(
                remaining,
                key=lambda p: haversine(cur_lat, cur_lng, float(p["lat"]), float(p["lng"])),
            )
            d = haversine(cur_lat, cur_lng, float(nearest["lat"]), float(nearest["lng"]))
            total += d
            nearest = dict(nearest)
            nearest["dist_km"] = round(d, 2)
            ordered.append(nearest)
            cur_lat, cur_lng = float(nearest["lat"]), float(nearest["lng"])
            remaining.remove(next(r for r in remaining if r["id"] == nearest["id"]))

        return ordered, round(total, 2)

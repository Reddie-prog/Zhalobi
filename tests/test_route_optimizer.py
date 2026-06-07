"""
Тесты оптимизатора маршрута бригады (TSP ближайшего соседа).
Покрывает: haversine, пустой список, один узел, порядок объезда,
поля результата, суммарное расстояние.
"""
import pytest
from backend.app.services.route_optimizer import RouteOptimizer, haversine


def make_point(id_, lat, lng, status="new", cat="Тест"):
    return {
        "id": id_,
        "ticket_number": f"ЖКХ-2024-{id_:05d}",
        "title": f"Инцидент #{id_}",
        "address": "ул. Тестовая, 1",
        "status": status,
        "lat": lat,
        "lng": lng,
        "category": cat,
    }


# ─── haversine ─────────────────────────────────────────────────────────────

class TestHaversine:
    def test_zero_distance(self):
        assert haversine(55.75, 37.62, 55.75, 37.62) == pytest.approx(0.0, abs=1e-9)

    def test_symmetry(self):
        a = haversine(55.75, 37.62, 55.80, 37.70)
        b = haversine(55.80, 37.70, 55.75, 37.62)
        assert a == pytest.approx(b, rel=1e-9)

    def test_non_negative(self):
        assert haversine(55.75, 37.62, 55.80, 37.70) > 0

    def test_moscow_spb(self):
        d = haversine(55.7558, 37.6176, 59.9343, 30.3351)
        assert 620 < d < 650

    def test_small_distance(self):
        # ≈100 м — разница 0.001° широты ≈ 0.11 км
        d = haversine(55.750, 37.620, 55.751, 37.620)
        assert 0.05 < d < 0.2


# ─── RouteOptimizer.optimize ───────────────────────────────────────────────

class TestRouteOptimizer:
    def setup_method(self):
        self.opt = RouteOptimizer()
        self.start = (55.750, 37.620)

    def test_empty_points_returns_empty(self):
        route, total = self.opt.optimize(*self.start, [])
        assert route == []
        assert total == 0.0

    def test_single_point(self):
        pt = make_point(1, 55.751, 37.620)
        route, total = self.opt.optimize(*self.start, [pt])
        assert len(route) == 1
        assert route[0]["id"] == 1
        assert total > 0

    def test_all_points_visited(self):
        points = [make_point(i, 55.75 + i * 0.01, 37.62) for i in range(1, 6)]
        route, _ = self.opt.optimize(*self.start, points)
        assert len(route) == 5
        visited_ids = {p["id"] for p in route}
        assert visited_ids == {1, 2, 3, 4, 5}

    def test_nearest_first(self):
        """Ближайшая к старту точка должна быть первой в маршруте."""
        far  = make_point(1, 55.800, 37.620)  # далеко
        near = make_point(2, 55.751, 37.620)  # близко
        route, _ = self.opt.optimize(*self.start, [far, near])
        assert route[0]["id"] == 2

    def test_dist_km_field_added(self):
        points = [make_point(i, 55.75 + i * 0.01, 37.62) for i in range(1, 4)]
        route, _ = self.opt.optimize(*self.start, points)
        for p in route:
            assert "dist_km" in p
            assert p["dist_km"] >= 0

    def test_total_is_sum_of_dist_km(self):
        points = [make_point(i, 55.75 + i * 0.01, 37.62) for i in range(1, 4)]
        route, total = self.opt.optimize(*self.start, points)
        calc = round(sum(p["dist_km"] for p in route), 2)
        assert total == pytest.approx(calc, abs=0.05)

    def test_total_is_non_negative(self):
        points = [make_point(i, 55.75 + i * 0.01, 37.62) for i in range(1, 4)]
        _, total = self.opt.optimize(*self.start, points)
        assert total >= 0

    def test_collinear_points_ordered_greedily(self):
        """Точки на одной широте по возрастанию lng: алгоритм должен идти слева направо."""
        points = [
            make_point(1, 55.750, 37.640),  # дальше
            make_point(2, 55.750, 37.622),  # ближе
            make_point(3, 55.750, 37.630),  # средний
        ]
        route, _ = self.opt.optimize(55.750, 37.620, points)
        assert route[0]["id"] == 2

    def test_original_points_not_mutated(self):
        """optimize не должен изменять входные точки."""
        original = make_point(1, 55.751, 37.620)
        pts = [original]
        self.opt.optimize(*self.start, pts)
        assert "dist_km" not in pts[0]

    def test_returns_tuple(self):
        result = self.opt.optimize(*self.start, [make_point(1, 55.751, 37.620)])
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_large_set_completes(self):
        """Не зависает на 100 точках."""
        import time
        points = [make_point(i, 55.75 + i * 0.001, 37.62 + i * 0.001) for i in range(1, 101)]
        t0 = time.time()
        route, _ = self.opt.optimize(*self.start, points)
        assert time.time() - t0 < 5.0
        assert len(route) == 100

    def test_string_coords_handled(self):
        """lat/lng могут прийти как строки из БД (lat = Column String)."""
        pt = make_point(1, "55.751", "37.622")
        route, _ = self.opt.optimize(*self.start, [pt])
        assert len(route) == 1

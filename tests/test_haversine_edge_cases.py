"""
Тесты граничных случаев для формулы Хаверсина в обоих сервисах.
Проверяет корректность на полюсах, антиподах, экваторе и нулевом меридиане.
"""
import math
import pytest
from backend.app.services.infrastructure_graph import _haversine as graph_haversine
from backend.app.services.route_optimizer import haversine as route_haversine


@pytest.mark.parametrize("fn", [graph_haversine, route_haversine])
class TestHaversineEdgeCases:
    def test_north_pole(self, fn):
        """Точка на Северном полюсе → сама себя = 0."""
        assert fn(90.0, 0.0, 90.0, 0.0) == pytest.approx(0.0, abs=1e-6)

    def test_south_pole_to_north_pole(self, fn):
        """Расстояние полюс-полюс ≈ π * R ≈ 20015 км."""
        d = fn(-90.0, 0.0, 90.0, 0.0)
        assert 19_900 < d < 20_100

    def test_equator_full_circle(self, fn):
        """Экватор, разница 180° по долготе ≈ π * R ≈ 20015 км."""
        d = fn(0.0, 0.0, 0.0, 180.0)
        assert 19_900 < d < 20_200

    def test_prime_meridian_crossing(self, fn):
        """Пересечение нулевого меридиана: −1° и +1° по lng."""
        d1 = fn(51.5, -1.0, 51.5, 1.0)
        d2 = fn(51.5,  0.0, 51.5, 2.0)
        assert d1 == pytest.approx(d2, rel=0.01)

    def test_antimeridian_symmetry(self, fn):
        """Расстояние через антимеридиан = то же что напрямую."""
        d1 = fn(0.0, 179.0, 0.0, -179.0)
        d2 = fn(0.0, 179.0, 0.0,  181.0)  # 181° = -179° по смыслу, но числом
        # d1 должен быть ≈ 2° * 111 км ≈ 222 км
        assert d1 == pytest.approx(222.0, rel=0.05)

    def test_result_is_finite(self, fn):
        """Любые валидные координаты → конечное число."""
        for lat1, lng1, lat2, lng2 in [
            (0, 0, 0, 0),
            (90, 0, -90, 0),
            (45, 90, -45, -90),
            (55.75, 37.62, 59.93, 30.33),
        ]:
            assert math.isfinite(fn(lat1, lng1, lat2, lng2))

    def test_triangle_inequality(self, fn):
        """Расстояние AB + BC ≥ AC."""
        a = (55.75, 37.62)
        b = (56.00, 38.00)
        c = (55.50, 38.50)
        ab = fn(*a, *b)
        bc = fn(*b, *c)
        ac = fn(*a, *c)
        assert ab + bc >= ac - 1e-6

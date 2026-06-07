"""
Тесты паттерна Observer: EventBus и EventType.
Покрывает: регистрацию подписчиков, публикацию событий,
параллельный вызов нескольких подписчиков, обработку ошибок внутри хендлеров.
"""
import asyncio
import pytest
from backend.app.patterns.observer import EventBus, EventType


pytestmark = pytest.mark.asyncio


# ─── Вспомогательные ───────────────────────────────────────────────────────

def make_tracker():
    """Возвращает async-хендлер и список вызовов для проверки."""
    calls = []

    async def handler(data):
        calls.append(data)

    return handler, calls


# ─── Регистрация ───────────────────────────────────────────────────────────

class TestSubscribe:
    def test_subscribe_stores_handler(self):
        bus = EventBus()
        handler, _ = make_tracker()
        bus.subscribe(EventType.CREATED, handler)
        assert handler in bus._subscribers[EventType.CREATED]

    def test_multiple_handlers_for_same_event(self):
        bus = EventBus()
        h1, _ = make_tracker()
        h2, _ = make_tracker()
        bus.subscribe(EventType.CREATED, h1)
        bus.subscribe(EventType.CREATED, h2)
        assert len(bus._subscribers[EventType.CREATED]) == 2

    def test_subscribe_different_events_independent(self):
        bus = EventBus()
        h1, _ = make_tracker()
        h2, _ = make_tracker()
        bus.subscribe(EventType.CREATED, h1)
        bus.subscribe(EventType.STATUS_CHANGED, h2)
        assert EventType.STATUS_CHANGED not in bus._subscribers.get(EventType.CREATED, [])


# ─── Публикация ────────────────────────────────────────────────────────────

class TestPublish:
    async def test_no_subscribers_no_error(self):
        bus = EventBus()
        await bus.publish(EventType.CREATED, {"id": 1})  # не должно падать

    async def test_subscriber_receives_data(self):
        bus = EventBus()
        handler, calls = make_tracker()
        bus.subscribe(EventType.CREATED, handler)
        await bus.publish(EventType.CREATED, {"id": 42})
        assert calls == [{"id": 42}]

    async def test_multiple_subscribers_all_called(self):
        bus = EventBus()
        h1, c1 = make_tracker()
        h2, c2 = make_tracker()
        bus.subscribe(EventType.ESCALATED, h1)
        bus.subscribe(EventType.ESCALATED, h2)
        await bus.publish(EventType.ESCALATED, "payload")
        assert c1 == ["payload"]
        assert c2 == ["payload"]

    async def test_wrong_event_not_triggered(self):
        bus = EventBus()
        handler, calls = make_tracker()
        bus.subscribe(EventType.CREATED, handler)
        await bus.publish(EventType.ESCALATED, {"id": 1})
        assert calls == []

    async def test_publish_unknown_event_no_error(self):
        bus = EventBus()
        await bus.publish("unknown.event", {})  # неизвестное событие — не падает

    async def test_data_passed_as_is(self):
        bus = EventBus()
        received = []

        async def capture(data):
            received.append(data)

        bus.subscribe(EventType.STATUS_CHANGED, capture)
        payload = {"complaint_id": 7, "new_status": "in_progress"}
        await bus.publish(EventType.STATUS_CHANGED, payload)
        assert received[0] is payload

    async def test_handler_called_once_per_publish(self):
        bus = EventBus()
        handler, calls = make_tracker()
        bus.subscribe(EventType.CREATED, handler)
        await bus.publish(EventType.CREATED, 1)
        await bus.publish(EventType.CREATED, 2)
        assert len(calls) == 2

    async def test_handler_receives_correct_data_on_multiple_publishes(self):
        bus = EventBus()
        handler, calls = make_tracker()
        bus.subscribe(EventType.CREATED, handler)
        await bus.publish(EventType.CREATED, "first")
        await bus.publish(EventType.CREATED, "second")
        assert calls[0] == "first"
        assert calls[1] == "second"


# ─── Устойчивость к ошибкам внутри хендлеров ──────────────────────────────

class TestErrorHandling:
    async def test_failing_handler_does_not_crash_bus(self):
        bus = EventBus()
        order = []

        async def bad_handler(data):
            raise ValueError("внутренняя ошибка")

        async def good_handler(data):
            order.append(data)

        bus.subscribe(EventType.CREATED, bad_handler)
        bus.subscribe(EventType.CREATED, good_handler)

        # Не должно упасть несмотря на ValueError в bad_handler
        await bus.publish(EventType.CREATED, "test")
        assert order == ["test"]

    async def test_all_handlers_called_despite_first_failing(self):
        bus = EventBus()
        calls = []

        async def fail(data):
            raise RuntimeError("fail")

        async def ok1(data):
            calls.append("ok1")

        async def ok2(data):
            calls.append("ok2")

        bus.subscribe(EventType.ASSIGNED, fail)
        bus.subscribe(EventType.ASSIGNED, ok1)
        bus.subscribe(EventType.ASSIGNED, ok2)

        await bus.publish(EventType.ASSIGNED, {})
        assert "ok1" in calls
        assert "ok2" in calls

    async def test_exception_in_handler_is_not_re_raised(self):
        bus = EventBus()

        async def always_fails(data):
            raise Exception("boom")

        bus.subscribe(EventType.RESOLVED, always_fails)

        # Не должно бросить исключение наружу
        try:
            await bus.publish(EventType.RESOLVED, {})
        except Exception:
            pytest.fail("EventBus.publish не должен пробрасывать исключения хендлеров")


# ─── EventType константы ───────────────────────────────────────────────────

class TestEventType:
    def test_all_event_types_are_strings(self):
        for attr in ("CREATED", "STATUS_CHANGED", "ESCALATED", "ASSIGNED", "RESOLVED"):
            val = getattr(EventType, attr)
            assert isinstance(val, str)

    def test_event_types_are_unique(self):
        values = [
            EventType.CREATED,
            EventType.STATUS_CHANGED,
            EventType.ESCALATED,
            EventType.ASSIGNED,
            EventType.RESOLVED,
        ]
        assert len(values) == len(set(values))

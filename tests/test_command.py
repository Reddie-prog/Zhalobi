"""
Тесты паттерна Command.
Покрывает: CommandHistory (push/pop/count), абстрактный базовый класс,
все конкретные команды через mock-сервис без БД.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from backend.app.patterns.command import (
    Command,
    CommandHistory,
    SubmitComplaintCommand,
    ChangeStatusCommand,
    EscalateComplaintCommand,
    AssignComplaintCommand,
)

pytestmark = pytest.mark.asyncio


# ─── CommandHistory ────────────────────────────────────────────────────────

class TestCommandHistory:
    def test_empty_history_count_is_zero(self):
        h = CommandHistory()
        assert h.count == 0

    def test_push_increases_count(self):
        h = CommandHistory()
        h.push(MagicMock())
        assert h.count == 1

    def test_pop_returns_last_pushed(self):
        h = CommandHistory()
        cmd1, cmd2 = MagicMock(), MagicMock()
        h.push(cmd1)
        h.push(cmd2)
        assert h.pop() is cmd2

    def test_pop_decreases_count(self):
        h = CommandHistory()
        h.push(MagicMock())
        h.pop()
        assert h.count == 0

    def test_pop_from_empty_returns_none(self):
        h = CommandHistory()
        assert h.pop() is None

    def test_lifo_order(self):
        h = CommandHistory()
        cmds = [MagicMock(name=str(i)) for i in range(3)]
        for c in cmds:
            h.push(c)
        for c in reversed(cmds):
            assert h.pop() is c

    def test_count_after_push_and_pop(self):
        h = CommandHistory()
        h.push(MagicMock())
        h.push(MagicMock())
        h.pop()
        assert h.count == 1


# ─── Command ABC ───────────────────────────────────────────────────────────

class TestCommandABC:
    def test_cannot_instantiate_abstract_command(self):
        with pytest.raises(TypeError):
            Command()

    def test_concrete_must_implement_execute_and_undo(self):
        class Incomplete(Command):
            async def execute(self):
                return None
            # undo не реализован

        with pytest.raises(TypeError):
            Incomplete()


# ─── SubmitComplaintCommand ────────────────────────────────────────────────

class TestSubmitComplaintCommand:
    def _make_complaint(self, id_=1, ticket="ЖКХ-2024-00001"):
        c = MagicMock()
        c.id = id_
        c.ticket_number = ticket
        return c

    async def test_execute_calls_create_complaint(self):
        svc = AsyncMock()
        svc.create_complaint.return_value = self._make_complaint()
        cmd = SubmitComplaintCommand(svc, user_id=42, data={"title": "Тест"})
        await cmd.execute()
        svc.create_complaint.assert_awaited_once_with(42, {"title": "Тест"})

    async def test_execute_returns_complaint(self):
        complaint = self._make_complaint(id_=7)
        svc = AsyncMock()
        svc.create_complaint.return_value = complaint
        cmd = SubmitComplaintCommand(svc, user_id=1, data={})
        result = await cmd.execute()
        assert result is complaint

    async def test_execute_stores_created_id(self):
        svc = AsyncMock()
        svc.create_complaint.return_value = self._make_complaint(id_=55)
        cmd = SubmitComplaintCommand(svc, user_id=1, data={})
        await cmd.execute()
        assert cmd._created_id == 55

    async def test_undo_calls_cancel_if_executed(self):
        svc = AsyncMock()
        svc.create_complaint.return_value = self._make_complaint(id_=3)
        cmd = SubmitComplaintCommand(svc, user_id=1, data={})
        await cmd.execute()
        await cmd.undo()
        svc.cancel_complaint.assert_awaited_once_with(3)

    async def test_undo_before_execute_does_nothing(self):
        svc = AsyncMock()
        cmd = SubmitComplaintCommand(svc, user_id=1, data={})
        await cmd.undo()  # не должно упасть
        svc.cancel_complaint.assert_not_awaited()


# ─── ChangeStatusCommand ───────────────────────────────────────────────────

class TestChangeStatusCommand:
    def _make_complaint(self, status="new"):
        c = MagicMock()
        c.status = status
        return c

    async def test_execute_calls_update_status(self):
        svc = AsyncMock()
        svc.get_complaint.return_value = self._make_complaint("new")
        svc.update_status.return_value = self._make_complaint("in_progress")
        cmd = ChangeStatusCommand(svc, complaint_id=1, new_status="in_progress",
                                  admin_id=99, comment="принято")
        await cmd.execute()
        svc.update_status.assert_awaited_once_with(1, "in_progress", 99, "принято")

    async def test_execute_saves_old_status(self):
        svc = AsyncMock()
        svc.get_complaint.return_value = self._make_complaint("new")
        svc.update_status.return_value = MagicMock()
        cmd = ChangeStatusCommand(svc, 1, "resolved", 1)
        await cmd.execute()
        assert cmd._old_status == "new"

    async def test_undo_restores_old_status(self):
        svc = AsyncMock()
        svc.get_complaint.return_value = self._make_complaint("new")
        svc.update_status.return_value = MagicMock()
        cmd = ChangeStatusCommand(svc, 1, "resolved", admin_id=1)
        await cmd.execute()
        await cmd.undo()
        # Второй вызов update_status должен восстановить "new"
        calls = svc.update_status.await_args_list
        assert calls[-1].args[1] == "new"

    async def test_execute_returns_service_result(self):
        svc = AsyncMock()
        expected = MagicMock()
        svc.get_complaint.return_value = self._make_complaint()
        svc.update_status.return_value = expected
        cmd = ChangeStatusCommand(svc, 1, "resolved", 1)
        result = await cmd.execute()
        assert result is expected


# ─── EscalateComplaintCommand ──────────────────────────────────────────────

class TestEscalateComplaintCommand:
    async def test_execute_calls_escalate(self):
        svc = AsyncMock()
        svc.escalate_complaint.return_value = MagicMock()
        cmd = EscalateComplaintCommand(svc, complaint_id=5, reason="просрочено")
        await cmd.execute()
        svc.escalate_complaint.assert_awaited_once_with(5, "просрочено")

    async def test_default_reason(self):
        svc = AsyncMock()
        svc.escalate_complaint.return_value = MagicMock()
        cmd = EscalateComplaintCommand(svc, complaint_id=1)
        await cmd.execute()
        args = svc.escalate_complaint.await_args.args
        assert args[1] == "Автоэскалация"

    async def test_undo_reverts_to_in_progress(self):
        svc = AsyncMock()
        svc.escalate_complaint.return_value = MagicMock()
        cmd = EscalateComplaintCommand(svc, complaint_id=3)
        await cmd.execute()
        await cmd.undo()
        svc.update_status.assert_awaited_once()
        call_args = svc.update_status.await_args.args
        assert call_args[1] == "in_progress"


# ─── AssignComplaintCommand ────────────────────────────────────────────────

class TestAssignComplaintCommand:
    def _make_complaint(self, assigned_to=None):
        c = MagicMock()
        c.assigned_to = assigned_to
        return c

    async def test_execute_calls_assign(self):
        svc = AsyncMock()
        svc.get_complaint.return_value = self._make_complaint()
        svc.assign_complaint.return_value = MagicMock()
        cmd = AssignComplaintCommand(svc, complaint_id=2, assignee_id=7, admin_id=1)
        await cmd.execute()
        svc.assign_complaint.assert_awaited_once_with(2, 7, 1)

    async def test_execute_stores_prev_assignee(self):
        svc = AsyncMock()
        svc.get_complaint.return_value = self._make_complaint(assigned_to=5)
        svc.assign_complaint.return_value = MagicMock()
        cmd = AssignComplaintCommand(svc, 2, 7, 1)
        await cmd.execute()
        assert cmd._prev_assignee == 5

    async def test_undo_restores_previous_assignee(self):
        svc = AsyncMock()
        svc.get_complaint.return_value = self._make_complaint(assigned_to=5)
        svc.assign_complaint.return_value = MagicMock()
        cmd = AssignComplaintCommand(svc, 2, 7, 1)
        await cmd.execute()
        await cmd.undo()
        calls = svc.assign_complaint.await_args_list
        # Последний вызов assign_complaint должен восстановить предыдущего исполнителя
        assert calls[-1].args[1] == 5

    async def test_can_assign_none(self):
        svc = AsyncMock()
        svc.get_complaint.return_value = self._make_complaint(assigned_to=3)
        svc.assign_complaint.return_value = MagicMock()
        cmd = AssignComplaintCommand(svc, 2, None, 1)
        await cmd.execute()
        svc.assign_complaint.assert_awaited_once_with(2, None, 1)

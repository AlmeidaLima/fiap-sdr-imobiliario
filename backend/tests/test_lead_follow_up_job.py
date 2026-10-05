from datetime import datetime, timezone
from unittest.mock import Mock

from app.jobs.lead_follow_up_job import LeadFollowUpJob


NOW = datetime(2026, 10, 2, 12, 0, tzinfo=timezone.utc)


def test_run_lists_due_pending_follow_ups():
    repository = Mock()
    repository.list_pending.return_value = []

    message_service = Mock()

    job = LeadFollowUpJob(
        follow_up_repository=repository,
        message_service=message_service,
        now_provider=lambda: NOW,
    )

    result = job.run()

    repository.list_pending.assert_called_once_with(
        due_before=NOW,
        limit=100,
    )

    assert result == []

def test_run_generates_message_for_due_follow_up():
    repository = Mock()

    follow_up = Mock()
    repository.list_pending.return_value = [follow_up]

    message_service = Mock()
    message_service.generate.return_value = "Mensagem de follow-up"

    job = LeadFollowUpJob(
        follow_up_repository=repository,
        message_service=message_service,
        now_provider=lambda: NOW,
    )

    result = job.run()

    message_service.generate.assert_called_once_with(follow_up)

    assert result == ["Mensagem de follow-up"]

    repository.create_attempt.assert_not_called()
    repository.update.assert_not_called()
    repository.commit.assert_not_called()

def test_run_generates_messages_for_multiple_due_follow_ups():
    repository = Mock()

    first_follow_up = Mock()
    second_follow_up = Mock()

    repository.list_pending.return_value = [
        first_follow_up,
        second_follow_up,
    ]

    message_service = Mock()
    message_service.generate.side_effect = [
        "Primeira mensagem",
        "Segunda mensagem",
    ]

    job = LeadFollowUpJob(
        follow_up_repository=repository,
        message_service=message_service,
        now_provider=lambda: NOW,
    )

    result = job.run()

    assert message_service.generate.call_count == 2

    message_service.generate.assert_any_call(first_follow_up)
    message_service.generate.assert_any_call(second_follow_up)

    assert result == [
        "Primeira mensagem",
        "Segunda mensagem",
    ]

def test_run_continues_when_message_generation_fails():
    repository = Mock()

    first_follow_up = Mock()
    second_follow_up = Mock()

    repository.list_pending.return_value = [
        first_follow_up,
        second_follow_up,
    ]

    message_service = Mock()
    message_service.generate.side_effect = [
        RuntimeError("Falha ao gerar mensagem"),
        "Segunda mensagem",
    ]

    job = LeadFollowUpJob(
        follow_up_repository=repository,
        message_service=message_service,
        now_provider=lambda: NOW,
    )

    result = job.run()

    assert message_service.generate.call_count == 2

    message_service.generate.assert_any_call(first_follow_up)
    message_service.generate.assert_any_call(second_follow_up)

    assert result == ["Segunda mensagem"]

def test_run_returns_empty_list_when_there_are_no_due_follow_ups():
    repository = Mock()
    repository.list_pending.return_value = []

    message_service = Mock()

    job = LeadFollowUpJob(
        follow_up_repository=repository,
        message_service=message_service,
        now_provider=lambda: NOW,
    )

    result = job.run()

    assert result == []

    message_service.generate.assert_not_called()


def test_run_requests_at_most_one_hundred_follow_ups():
    repository = Mock()
    repository.list_pending.return_value = []

    message_service = Mock()

    job = LeadFollowUpJob(
        follow_up_repository=repository,
        message_service=message_service,
        now_provider=lambda: NOW,
    )

    job.run()

    repository.list_pending.assert_called_once_with(
        due_before=NOW,
        limit=100,
    )


def test_run_preserves_repository_order():
    repository = Mock()

    first_follow_up = Mock()
    second_follow_up = Mock()
    third_follow_up = Mock()

    repository.list_pending.return_value = [
        first_follow_up,
        second_follow_up,
        third_follow_up,
    ]

    message_service = Mock()
    message_service.generate.side_effect = [
        "Primeira mensagem",
        "Segunda mensagem",
        "Terceira mensagem",
    ]

    job = LeadFollowUpJob(
        follow_up_repository=repository,
        message_service=message_service,
        now_provider=lambda: NOW,
    )

    result = job.run()

    assert result == [
        "Primeira mensagem",
        "Segunda mensagem",
        "Terceira mensagem",
    ]

    assert message_service.generate.call_args_list == [
        ((first_follow_up,),),
        ((second_follow_up,),),
        ((third_follow_up,),),
    ]


from datetime import datetime, timedelta, timezone
import logging
from unittest.mock import Mock

from app.jobs.lead_follow_up_job import LeadFollowUpJob


NOW = datetime(2026, 10, 5, 12, 0, tzinfo=timezone.utc)


def follow_up(identifier: int, minutes: int = 0):
    item = Mock()
    item.id = identifier
    item.lead_id = identifier * 10
    item.scheduled_at = NOW + timedelta(minutes=minutes)
    return item


def make_job(repository, delivery):
    return LeadFollowUpJob(
        follow_up_repository=repository,
        delivery_service=delivery,
        now_provider=lambda: NOW,
        logger=Mock(),
    )


def test_run_empty_cycle():
    repository = Mock()
    repository.claim_next_pending.return_value = None
    result = make_job(repository, Mock()).run()
    assert result.processed == 0
    repository.claim_next_pending.assert_called_once_with(
        due_before=NOW,
        cursor=None,
    )


def test_run_delivers_multiple_follow_ups_and_advances_cursor():
    first = follow_up(1, -2)
    second = follow_up(2, -1)
    repository = Mock()
    repository.claim_next_pending.side_effect = [first, second, None]
    delivery = Mock()
    delivery.deliver_claimed.return_value = Mock(
        conversation_id="conversation",
        attempt=Mock(attempt_number=1),
    )

    result = make_job(repository, delivery).run()

    assert result.processed == 2
    assert result.delivered == 2
    assert repository.claim_next_pending.call_args_list[1].kwargs["cursor"] == (
        first.scheduled_at,
        first.id,
    )
    assert repository.claim_next_pending.call_args_list[2].kwargs["cursor"] == (
        second.scheduled_at,
        second.id,
    )


def test_failure_advances_cursor_and_does_not_repeat_in_cycle():
    failed = follow_up(1, -2)
    next_item = follow_up(2, -1)
    repository = Mock()
    repository.claim_next_pending.side_effect = [failed, next_item, None]
    delivery = Mock()
    delivery.deliver_claimed.side_effect = [
        RuntimeError("database unavailable"),
        Mock(conversation_id="conversation", attempt=Mock(attempt_number=1)),
    ]

    result = make_job(repository, delivery).run()

    assert result.processed == 2
    assert result.failed == 1
    assert result.delivered == 1
    assert delivery.deliver_claimed.call_count == 2
    assert repository.claim_next_pending.call_args_list[1].kwargs["cursor"] == (
        failed.scheduled_at,
        failed.id,
    )


def test_skipped_follow_up_does_not_stop_cycle():
    first = follow_up(1)
    repository = Mock()
    repository.claim_next_pending.side_effect = [first, None]
    delivery = Mock()
    delivery.deliver_claimed.return_value = None
    result = make_job(repository, delivery).run()
    assert result.skipped == 1
    assert result.failed == 0


def test_more_than_one_hundred_are_processed_in_same_cycle():
    items = [follow_up(index, index - 150) for index in range(1, 102)]
    repository = Mock()
    repository.claim_next_pending.side_effect = [*items, None]
    delivery = Mock()
    delivery.deliver_claimed.return_value = Mock(
        conversation_id="conversation",
        attempt=Mock(attempt_number=1),
    )
    logger = Mock()
    job = LeadFollowUpJob(
        follow_up_repository=repository,
        delivery_service=delivery,
        now_provider=lambda: NOW,
        logger=logger,
    )

    result = job.run()

    assert result.processed == 101
    assert result.delivered == 101
    assert repository.claim_next_pending.call_count == 102
    assert sum(
        call.args[0] == "follow_up_batch_completed"
        for call in logger.info.call_args_list
    ) == 2


def test_stop_requested_after_first_delivery_prevents_next_claim():
    first = follow_up(1)
    repository = Mock()
    repository.claim_next_pending.side_effect = [first, follow_up(2), None]
    stop_requested = False
    delivery = Mock()

    def deliver(follow_up=None, due_before=None):
        nonlocal stop_requested
        stop_requested = True
        return Mock(conversation_id="conversation", attempt=Mock(attempt_number=1))

    delivery.deliver_claimed.side_effect = deliver
    job = LeadFollowUpJob(
        follow_up_repository=repository,
        delivery_service=delivery,
        now_provider=lambda: NOW,
        logger=Mock(),
        should_stop=lambda: stop_requested,
    )

    result = job.run()

    assert result.processed == 1
    repository.claim_next_pending.assert_called_once_with(
        due_before=NOW,
        cursor=None,
    )


def test_processing_failure_log_does_not_include_exception_text(caplog):
    repository = Mock()
    repository.claim_next_pending.side_effect = [follow_up(1), None]
    delivery = Mock()
    delivery.deliver_claimed.side_effect = RuntimeError(
        "SEGREDO_TESTE_FOLLOW_UP"
    )
    logger = logging.getLogger("test_safe_follow_up_job")

    with caplog.at_level(logging.ERROR, logger=logger.name):
        LeadFollowUpJob(
            follow_up_repository=repository,
            delivery_service=delivery,
            now_provider=lambda: NOW,
            logger=logger,
        ).run()

    assert "follow_up_processing_failed" in caplog.text
    assert "SEGREDO_TESTE_FOLLOW_UP" not in caplog.text

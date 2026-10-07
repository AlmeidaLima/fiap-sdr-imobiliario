import logging
import threading
from unittest.mock import Mock, patch

from sqlalchemy.orm import configure_mappers

from scripts.run_lead_follow_up_worker import run_worker


def test_worker_bootstrap_loads_required_models():
    configure_mappers()


@patch("scripts.run_lead_follow_up_worker.signal.signal")
@patch("scripts.run_lead_follow_up_worker._create_job")
@patch("scripts.run_lead_follow_up_worker.SessionLocal")
def test_worker_runs_cycle_closes_session_and_stops(
        session_local,
        create_job,
        signal_mock,
):
    db = Mock()
    session_local.return_value = db
    stop_event = Mock(spec=threading.Event)
    stop_event.is_set.side_effect = [False, True]

    run_worker(stop_event=stop_event, interval_seconds=30)

    create_job.assert_called_once_with(
        db,
        should_stop=stop_event.is_set,
    )
    create_job.return_value.run.assert_called_once_with()
    db.close.assert_called_once_with()
    stop_event.wait.assert_called_once_with(30)
    assert signal_mock.call_count == 2


@patch("scripts.run_lead_follow_up_worker.signal.signal")
@patch("scripts.run_lead_follow_up_worker._create_job")
@patch("scripts.run_lead_follow_up_worker.SessionLocal")
def test_database_failure_does_not_terminate_worker(
        session_local,
        create_job,
        _signal_mock,
):
    first_db = Mock()
    second_db = Mock()
    session_local.side_effect = [first_db, second_db]
    first_job = Mock()
    first_job.run.side_effect = RuntimeError("database unavailable")
    second_job = Mock()
    create_job.side_effect = [first_job, second_job]
    stop_event = Mock(spec=threading.Event)
    stop_event.is_set.side_effect = [False, False, True]

    run_worker(stop_event=stop_event, interval_seconds=30)

    first_db.rollback.assert_called_once_with()
    first_db.close.assert_called_once_with()
    second_job.run.assert_called_once_with()
    second_db.close.assert_called_once_with()
    assert stop_event.wait.call_count == 2


@patch("scripts.run_lead_follow_up_worker.signal.signal")
@patch("scripts.run_lead_follow_up_worker.SessionLocal")
def test_sigterm_handler_requests_graceful_shutdown(session_local, signal_mock):
    stop_event = Mock(spec=threading.Event)
    stop_event.is_set.return_value = True

    run_worker(stop_event=stop_event)

    term_handler = signal_mock.call_args_list[0].args[1]
    term_handler(15, None)
    stop_event.set.assert_called_once_with()
    session_local.assert_not_called()


@patch("scripts.run_lead_follow_up_worker.signal.signal")
@patch("scripts.run_lead_follow_up_worker._create_job")
@patch("scripts.run_lead_follow_up_worker.SessionLocal")
def test_database_failure_log_does_not_include_exception_text(
        session_local,
        create_job,
        _signal_mock,
        caplog,
):
    db = Mock()
    session_local.return_value = db
    create_job.return_value.run.side_effect = RuntimeError(
        "SEGREDO_TESTE_FOLLOW_UP"
    )
    stop_event = Mock(spec=threading.Event)
    stop_event.is_set.side_effect = [False, True]

    with caplog.at_level(logging.ERROR, logger="follow_up_worker"):
        run_worker(stop_event=stop_event, interval_seconds=30)

    assert "follow_up_database_unavailable" in caplog.text
    assert "SEGREDO_TESTE_FOLLOW_UP" not in caplog.text

from unittest.mock import Mock, patch

from scripts.process_lead_follow_ups import (
    process_lead_follow_ups,
)


@patch("scripts.process_lead_follow_ups.LeadFollowUpJob")
@patch("scripts.process_lead_follow_ups.LeadFollowUpMessageService")
@patch("scripts.process_lead_follow_ups.LeadFollowUpRepository")
@patch("scripts.process_lead_follow_ups.SessionLocal")
def test_process_lead_follow_ups_executes_job(
        session_local_mock,
        repository_class_mock,
        message_service_class_mock,
        job_class_mock,
):
    db = Mock()
    session_local_mock.return_value = db

    repository = Mock()
    repository_class_mock.return_value = repository

    message_service = Mock()
    message_service_class_mock.return_value = message_service

    job = Mock()
    job.run.return_value = [
        "Primeira mensagem",
        "Segunda mensagem",
    ]
    job_class_mock.return_value = job

    result = process_lead_follow_ups()

    session_local_mock.assert_called_once_with()

    repository_class_mock.assert_called_once_with(db)
    message_service_class_mock.assert_called_once_with()

    job_class_mock.assert_called_once_with(
        follow_up_repository=repository,
        message_service=message_service,
    )

    job.run.assert_called_once_with()

    assert result == [
        "Primeira mensagem",
        "Segunda mensagem",
    ]

    db.close.assert_called_once_with()


@patch("scripts.process_lead_follow_ups.LeadFollowUpJob")
@patch("scripts.process_lead_follow_ups.LeadFollowUpMessageService")
@patch("scripts.process_lead_follow_ups.LeadFollowUpRepository")
@patch("scripts.process_lead_follow_ups.SessionLocal")
def test_process_lead_follow_ups_returns_empty_list(
        session_local_mock,
        repository_class_mock,
        message_service_class_mock,
        job_class_mock,
):
    db = Mock()
    session_local_mock.return_value = db

    repository_class_mock.return_value = Mock()
    message_service_class_mock.return_value = Mock()

    job = Mock()
    job.run.return_value = []
    job_class_mock.return_value = job

    result = process_lead_follow_ups()

    assert result == []

    db.close.assert_called_once_with()


@patch("scripts.process_lead_follow_ups.LeadFollowUpJob")
@patch("scripts.process_lead_follow_ups.LeadFollowUpMessageService")
@patch("scripts.process_lead_follow_ups.LeadFollowUpRepository")
@patch("scripts.process_lead_follow_ups.SessionLocal")
def test_process_lead_follow_ups_closes_session_when_job_fails(
        session_local_mock,
        repository_class_mock,
        message_service_class_mock,
        job_class_mock,
):
    db = Mock()
    session_local_mock.return_value = db

    repository_class_mock.return_value = Mock()
    message_service_class_mock.return_value = Mock()

    job = Mock()
    job.run.side_effect = RuntimeError(
        "Falha durante processamento"
    )
    job_class_mock.return_value = job

    try:
        process_lead_follow_ups()
    except RuntimeError:
        pass

    db.close.assert_called_once_with()


@patch("scripts.process_lead_follow_ups.LeadFollowUpJob")
@patch("scripts.process_lead_follow_ups.LeadFollowUpMessageService")
@patch("scripts.process_lead_follow_ups.LeadFollowUpRepository")
@patch("scripts.process_lead_follow_ups.SessionLocal")
def test_process_lead_follow_ups_does_not_persist_contact(
        session_local_mock,
        repository_class_mock,
        message_service_class_mock,
        job_class_mock,
):
    db = Mock()
    session_local_mock.return_value = db

    repository = Mock()
    repository_class_mock.return_value = repository

    message_service_class_mock.return_value = Mock()

    job = Mock()
    job.run.return_value = ["Mensagem"]
    job_class_mock.return_value = job

    process_lead_follow_ups()

    repository.create_attempt.assert_not_called()
    repository.update.assert_not_called()
    repository.commit.assert_not_called()

    db.commit.assert_not_called()
    db.close.assert_called_once_with()
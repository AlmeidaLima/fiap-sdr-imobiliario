import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock



from app.core.exceptions import ApplicationException
from app.models.lead import Lead
from app.models.property import Property
from app.models.appointment import Appointment
from app.models.lead_follow_up import LeadFollowUp
from app.models.lead_follow_up_attempt import LeadFollowUpAttempt
from app.services.lead_follow_up_service import LeadFollowUpService

NOW = datetime(2026, 9, 30, 12, 0, tzinfo=timezone.utc)


@pytest.fixture
def repository():
    repo = Mock()
    repo.get_by_idempotency_key.return_value = None
    repo.create.side_effect = lambda follow_up: follow_up
    return repo


@pytest.fixture
def service(repository):
    return LeadFollowUpService(
        follow_up_repository=repository,
        now_provider=lambda: NOW,
    )


def test_schedule_accepts_appointment_from_same_lead(repository):
    appointment_repository = Mock()
    appointment_repository.get_by_id.return_value = Appointment(
        id=20,
        lead_id=10,
        appointment_type="REUNIAO",
        scheduled_at=NOW,
        status="CONFIRMED",
        idempotency_key="appointment-same-lead",
    )
    service = LeadFollowUpService(
        follow_up_repository=repository,
        appointment_repository=appointment_repository,
        now_provider=lambda: NOW,
    )

    result = service.schedule(
        lead_id=10,
        appointment_id=20,
        scheduled_at=NOW + timedelta(days=1),
    )

    assert result.appointment_id == 20
    repository.create.assert_called_once()


@pytest.mark.parametrize(
    ("appointment", "expected_error"),
    [
        (None, "appointment_not_found"),
        (
            Appointment(
                id=20,
                lead_id=11,
                appointment_type="REUNIAO",
                scheduled_at=NOW,
                status="CONFIRMED",
                idempotency_key="appointment-other-lead",
            ),
            "appointment_lead_mismatch",
        ),
    ],
)
def test_schedule_rejects_invalid_appointment_relationship(
        repository,
        appointment,
        expected_error,
):
    appointment_repository = Mock()
    appointment_repository.get_by_id.return_value = appointment
    service = LeadFollowUpService(
        follow_up_repository=repository,
        appointment_repository=appointment_repository,
        now_provider=lambda: NOW,
    )

    with pytest.raises(ApplicationException) as caught:
        service.schedule(
            lead_id=10,
            appointment_id=20,
            scheduled_at=NOW + timedelta(days=1),
        )

    assert caught.value.error == expected_error
    repository.get_by_idempotency_key.assert_not_called()
    repository.create.assert_not_called()
    repository.commit.assert_not_called()


def test_schedule_creates_pending_follow_up(service, repository):
    scheduled_at = NOW + timedelta(days=1)

    result = service.schedule(
        lead_id=10,
        scheduled_at=scheduled_at,
    )

    assert isinstance(result, LeadFollowUp)
    assert result.lead_id == 10
    assert result.status == "PENDING"
    assert result.scheduled_at == scheduled_at
    assert len(result.idempotency_key) == 64
    repository.create.assert_called_once()
    repository.commit.assert_called_once_with()

def test_schedule_returns_existing_follow_up(service, repository):
    scheduled_at = NOW + timedelta(days=1)

    existing = LeadFollowUp(
        id=5,
        lead_id=10,
        status="PENDING",
        scheduled_at=scheduled_at,
        idempotency_key="existing-key",
    )
    repository.get_by_idempotency_key.return_value = existing

    result = service.schedule(
        lead_id=10,
        scheduled_at=scheduled_at,
    )

    assert result is existing
    repository.create.assert_not_called()
    repository.commit.assert_not_called()

def test_schedule_rejects_past_date(service, repository):
    with pytest.raises(ApplicationException):
        service.schedule(
            lead_id=10,
            scheduled_at=NOW - timedelta(minutes=1),
        )

    repository.create.assert_not_called()


def test_schedule_rejects_naive_datetime(service, repository):
    with pytest.raises(ApplicationException):
        service.schedule(
            lead_id=10,
            scheduled_at=datetime(2026, 10, 1, 12, 0),
        )

    repository.create.assert_not_called()


def test_schedule_rejects_invalid_lead_id(service, repository):
    with pytest.raises(ApplicationException):
        service.schedule(
            lead_id=0,
            scheduled_at=NOW + timedelta(days=1),
        )

    repository.create.assert_not_called()


def test_idempotency_key_is_deterministic():
    scheduled_at = NOW + timedelta(days=1)

    first = LeadFollowUpService.build_idempotency_key(
        lead_id=10,
        appointment_id=20,
        scheduled_at=scheduled_at,
    )
    second = LeadFollowUpService.build_idempotency_key(
        lead_id=10,
        appointment_id=20,
        scheduled_at=scheduled_at,
    )

    assert first == second
    assert len(first) == 64


def test_get_by_id_returns_existing_follow_up(service, repository):
    existing = LeadFollowUp(
        id=5,
        lead_id=10,
        status="PENDING",
        scheduled_at=NOW + timedelta(days=1),
        idempotency_key="existing-key",
    )
    repository.get_by_id.return_value = existing

    result = service.get_by_id(5)

    assert result is existing
    repository.get_by_id.assert_called_once_with(5)


def test_get_by_id_raises_when_not_found(service, repository):
    repository.get_by_id.return_value = None

    with pytest.raises(ApplicationException):
        service.get_by_id(999)

# ============================================================
# TESTES DE CANCELAMENTO
# ============================================================


def test_cancel_pending_follow_up(service, repository):
    follow_up = LeadFollowUp(
        id=5,
        lead_id=10,
        status="PENDING",
        scheduled_at=NOW + timedelta(days=1),
        idempotency_key="cancel-test",
    )

    repository.get_by_id.return_value = follow_up
    repository.update.side_effect = lambda item: item

    result = service.cancel(5)

    assert result.status == "CANCELLED"
    repository.update.assert_called_once_with(follow_up)
    repository.commit.assert_called_once_with()

def test_cancel_already_cancelled_is_idempotent(service, repository):
    follow_up = LeadFollowUp(
        id=5,
        lead_id=10,
        status="CANCELLED",
        scheduled_at=NOW + timedelta(days=1),
        idempotency_key="cancel-test",
    )

    repository.get_by_id.return_value = follow_up

    result = service.cancel(5)

    assert result is follow_up
    repository.update.assert_not_called()
    repository.commit.assert_not_called()


def test_cancel_completed_follow_up_is_rejected(service, repository):
    follow_up = LeadFollowUp(
        id=5,
        lead_id=10,
        status="COMPLETED",
        scheduled_at=NOW + timedelta(days=1),
        idempotency_key="cancel-test",
    )

    repository.get_by_id.return_value = follow_up

    with pytest.raises(ApplicationException):
        service.cancel(5)

    repository.update.assert_not_called()


def test_cancel_nonexistent_follow_up(service, repository):
    repository.get_by_id.return_value = None

    with pytest.raises(ApplicationException):
        service.cancel(999)

    repository.update.assert_not_called()

# ============================================================
# TESTES DE CONCLUSÃO
# ============================================================


def test_complete_pending_follow_up(service, repository):
    follow_up = LeadFollowUp(
        id=5,
        lead_id=10,
        status="PENDING",
        scheduled_at=NOW + timedelta(days=1),
        idempotency_key="complete-test",
    )

    repository.get_by_id.return_value = follow_up
    repository.update.side_effect = lambda item: item

    result = service.complete(5)

    assert result.status == "COMPLETED"
    assert result.completed_at == NOW
    repository.update.assert_called_once_with(follow_up)
    repository.commit.assert_called_once_with()

def test_complete_already_completed_is_idempotent(service, repository):
    completed_at = NOW - timedelta(hours=1)

    follow_up = LeadFollowUp(
        id=5,
        lead_id=10,
        status="COMPLETED",
        scheduled_at=NOW - timedelta(days=1),
        completed_at=completed_at,
        idempotency_key="complete-test",
    )

    repository.get_by_id.return_value = follow_up

    result = service.complete(5)

    assert result is follow_up
    assert result.completed_at == completed_at
    repository.update.assert_not_called()
    repository.commit.assert_not_called()

def test_complete_cancelled_follow_up_is_rejected(service, repository):
    follow_up = LeadFollowUp(
        id=5,
        lead_id=10,
        status="CANCELLED",
        scheduled_at=NOW + timedelta(days=1),
        idempotency_key="complete-test",
    )

    repository.get_by_id.return_value = follow_up

    with pytest.raises(ApplicationException):
        service.complete(5)

    repository.update.assert_not_called()


def test_complete_nonexistent_follow_up(service, repository):
    repository.get_by_id.return_value = None

    with pytest.raises(ApplicationException):
        service.complete(999)

    repository.update.assert_not_called()

# ============================================================
# TESTES DE TENTATIVAS
# ============================================================

def test_register_failed_attempt_keeps_follow_up_pending(
        service,
        repository,
):
    follow_up = LeadFollowUp(
        id=5,
        lead_id=10,
        status="PENDING",
        scheduled_at=NOW + timedelta(days=1),
        attempt_count=0,
        idempotency_key="attempt-test",
    )

    repository.get_by_id_for_update.return_value = follow_up
    repository.create_attempt.side_effect = lambda attempt: attempt
    repository.update.side_effect = lambda item: item

    result = service.register_attempt(
        follow_up_id=5,
        channel="MANUAL",
        status="FAILED",
        message="Não foi possível falar com o lead.",
    )

    assert isinstance(result, LeadFollowUpAttempt)
    assert result.follow_up_id == 5
    assert result.attempt_number == 1
    assert result.channel == "MANUAL"
    assert result.status == "FAILED"
    assert result.executed_at == NOW

    assert follow_up.attempt_count == 1
    assert follow_up.status == "PENDING"
    assert follow_up.completed_at is None

    repository.create_attempt.assert_called_once()
    repository.update.assert_called_once_with(follow_up)
    repository.commit.assert_called_once()
    repository.rollback.assert_not_called()

def test_register_successful_attempt_completes_follow_up(
        service,
        repository,
):
    follow_up = LeadFollowUp(
        id=5,
        lead_id=10,
        status="PENDING",
        scheduled_at=NOW + timedelta(days=1),
        attempt_count=1,
        idempotency_key="attempt-success-test",
    )

    repository.get_by_id_for_update.return_value = follow_up
    repository.create_attempt.side_effect = lambda attempt: attempt
    repository.update.side_effect = lambda item: item

    result = service.register_attempt(
        follow_up_id=5,
        channel="MANUAL",
        status="SUCCESS",
        message="Contato realizado com o lead.",
    )

    assert isinstance(result, LeadFollowUpAttempt)
    assert result.follow_up_id == 5
    assert result.attempt_number == 2
    assert result.channel == "MANUAL"
    assert result.status == "SUCCESS"
    assert result.executed_at == NOW

    assert follow_up.attempt_count == 2
    assert follow_up.status == "COMPLETED"
    assert follow_up.completed_at == NOW

    repository.create_attempt.assert_called_once()
    repository.update.assert_called_once_with(follow_up)
    repository.commit.assert_called_once()
    repository.rollback.assert_not_called()

def test_register_attempt_rejects_cancelled_follow_up(
        service,
        repository,
):
    follow_up = LeadFollowUp(
        id=5,
        lead_id=10,
        status="CANCELLED",
        scheduled_at=NOW + timedelta(days=1),
        attempt_count=0,
        idempotency_key="attempt-cancelled-test",
    )

    repository.get_by_id_for_update.return_value = follow_up

    with pytest.raises(ApplicationException):
        service.register_attempt(
            follow_up_id=5,
            channel="MANUAL",
            status="FAILED",
            message="Tentativa de contato.",
        )

    repository.create_attempt.assert_not_called()
    repository.update.assert_not_called()
    repository.commit.assert_not_called()
    repository.rollback.assert_called_once()

def test_register_attempt_rejects_completed_follow_up(
        service,
        repository,
):
    follow_up = LeadFollowUp(
        id=5,
        lead_id=10,
        status="COMPLETED",
        scheduled_at=NOW - timedelta(days=1),
        completed_at=NOW,
        attempt_count=1,
        idempotency_key="attempt-completed-test",
    )

    repository.get_by_id_for_update.return_value = follow_up

    with pytest.raises(ApplicationException):
        service.register_attempt(
            follow_up_id=5,
            channel="MANUAL",
            status="FAILED",
            message="Nova tentativa indevida.",
        )

    repository.create_attempt.assert_not_called()
    repository.update.assert_not_called()
    repository.commit.assert_not_called()
    repository.rollback.assert_called_once()

def test_register_attempt_rejects_invalid_channel(
        service,
        repository,
):
    with pytest.raises(ApplicationException):
        service.register_attempt(
            follow_up_id=5,
            channel="SMS",
            status="FAILED",
            message="Tentativa de contato.",
        )

    repository.get_by_id_for_update.assert_not_called()
    repository.create_attempt.assert_not_called()
    repository.update.assert_not_called()
    repository.commit.assert_not_called()
    repository.rollback.assert_not_called()


def test_register_attempt_accepts_web_channel(service, repository):
    follow_up = LeadFollowUp(
        id=5,
        lead_id=10,
        status="PENDING",
        scheduled_at=NOW,
        attempt_count=0,
        idempotency_key="web-channel",
    )
    repository.get_by_id_for_update.return_value = follow_up
    repository.create_attempt.side_effect = lambda attempt: attempt
    repository.update.side_effect = lambda item: item

    attempt = service.register_attempt(
        follow_up_id=5,
        channel="WEB",
        status="SUCCESS",
        message="Follow-up web",
    )

    assert attempt.channel == "WEB"
    assert attempt.status == "SUCCESS"

def test_register_attempt_rejects_invalid_status(
        service,
        repository,
):
    with pytest.raises(ApplicationException):
        service.register_attempt(
            follow_up_id=5,
            channel="MANUAL",
            status="PENDING",
            message="Tentativa de contato.",
        )

    repository.get_by_id_for_update.assert_not_called()
    repository.create_attempt.assert_not_called()
    repository.update.assert_not_called()
    repository.commit.assert_not_called()
    repository.rollback.assert_not_called()

def test_register_attempt_rejects_nonexistent_follow_up(
        service,
        repository,
):
    repository.get_by_id_for_update.return_value = None

    with pytest.raises(ApplicationException):
        service.register_attempt(
            follow_up_id=999,
            channel="MANUAL",
            status="FAILED",
            message="Tentativa de contato.",
        )

    repository.get_by_id_for_update.assert_called_once_with(999)
    repository.create_attempt.assert_not_called()
    repository.update.assert_not_called()
    repository.commit.assert_not_called()
    repository.rollback.assert_called_once()

def test_register_attempt_rolls_back_when_create_attempt_fails(
        service,
        repository,
):
    follow_up = LeadFollowUp(
        id=5,
        lead_id=10,
        status="PENDING",
        scheduled_at=NOW + timedelta(days=1),
        attempt_count=0,
        idempotency_key="attempt-rollback-test",
    )

    repository.get_by_id_for_update.return_value = follow_up
    repository.create_attempt.side_effect = RuntimeError(
        "Erro ao persistir tentativa."
    )

    with pytest.raises(RuntimeError):
        service.register_attempt(
            follow_up_id=5,
            channel="MANUAL",
            status="FAILED",
            message="Tentativa de contato.",
        )

    repository.create_attempt.assert_called_once()
    repository.update.assert_not_called()
    repository.commit.assert_not_called()
    repository.rollback.assert_called_once()

def test_schedule_rolls_back_when_create_fails(repository):
    repository.create.side_effect = RuntimeError(
        "Falha ao criar follow-up"
    )

    service = LeadFollowUpService(
        follow_up_repository=repository,
        now_provider=lambda: NOW,
    )

    scheduled_at = NOW + timedelta(days=1)

    with pytest.raises(RuntimeError):
        service.schedule(
            lead_id=1,
            scheduled_at=scheduled_at,
        )

    repository.rollback.assert_called_once_with()
    repository.commit.assert_not_called()


def test_cancel_rolls_back_when_update_fails(repository):
    follow_up = LeadFollowUp(
        id=1,
        lead_id=1,
        status="PENDING",
        scheduled_at=NOW + timedelta(days=1),
        idempotency_key="test-key",
    )

    repository.get_by_id.return_value = follow_up
    repository.update.side_effect = RuntimeError(
        "Falha ao cancelar follow-up"
    )

    service = LeadFollowUpService(
        follow_up_repository=repository,
        now_provider=lambda: NOW,
    )

    with pytest.raises(RuntimeError):
        service.cancel(1)

    repository.rollback.assert_called_once_with()
    repository.commit.assert_not_called()


def test_complete_rolls_back_when_update_fails(repository):
    follow_up = LeadFollowUp(
        id=1,
        lead_id=1,
        status="PENDING",
        scheduled_at=NOW + timedelta(days=1),
        idempotency_key="test-key",
    )

    repository.get_by_id.return_value = follow_up
    repository.update.side_effect = RuntimeError(
        "Falha ao concluir follow-up"
    )

    service = LeadFollowUpService(
        follow_up_repository=repository,
        now_provider=lambda: NOW,
    )

    with pytest.raises(RuntimeError):
        service.complete(1)

    repository.rollback.assert_called_once_with()
    repository.commit.assert_not_called()

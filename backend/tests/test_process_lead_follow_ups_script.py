from unittest.mock import Mock, patch

from app.jobs.lead_follow_up_job import LeadFollowUpJobResult
from scripts.process_lead_follow_ups import process_lead_follow_ups


@patch("scripts.process_lead_follow_ups.LeadFollowUpJob")
@patch("scripts.process_lead_follow_ups.SessionLocal")
def test_process_lead_follow_ups_executes_job(session_local, job_class):
    db = Mock()
    session_local.return_value = db
    expected = LeadFollowUpJobResult(processed=2, delivered=1, skipped=1)
    job_class.return_value.run.return_value = expected

    result = process_lead_follow_ups()

    assert result == expected
    job_class.return_value.run.assert_called_once_with()
    db.close.assert_called_once_with()


@patch("scripts.process_lead_follow_ups.LeadFollowUpJob")
@patch("scripts.process_lead_follow_ups.SessionLocal")
def test_process_lead_follow_ups_closes_session_when_job_fails(
        session_local,
        job_class,
):
    db = Mock()
    session_local.return_value = db
    job_class.return_value.run.side_effect = RuntimeError("failure")

    try:
        process_lead_follow_ups()
    except RuntimeError:
        pass

    db.close.assert_called_once_with()

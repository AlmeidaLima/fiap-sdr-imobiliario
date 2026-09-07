from app.schemas.error import ErrorResponse


def test_error_response_accepts_string_detail():
    error = ErrorResponse(
        error="application_error",
        detail="Erro de teste",
    )

    assert error.error == "application_error"
    assert error.detail == "Erro de teste"


def test_error_response_accepts_validation_detail():
    error = ErrorResponse(
        error="validation_error",
        detail=[
            {
                "type": "missing",
                "loc": ["body", "name"],
                "msg": "Field required",
                "input": {},
            }
        ],
    )

    assert error.error == "validation_error"
    assert isinstance(error.detail, list)
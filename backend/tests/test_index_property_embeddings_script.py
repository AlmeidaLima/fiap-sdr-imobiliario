from types import SimpleNamespace
from unittest.mock import Mock, patch

from scripts.index_property_embeddings import index_embeddings, main


SENSITIVE_VALUE = "SEGREDO_TESTE_INDEXACAO"
AUDIT_SENSITIVE_VALUE = "SEGREDO_AUDITORIA_RNF006"


def _database_with_batches(*batches):
    database = Mock()
    database.execute.return_value.scalars.return_value.all.side_effect = batches
    return database


@patch("scripts.index_property_embeddings.EmbeddingService")
@patch("scripts.index_property_embeddings.PropertyDocumentService")
@patch("scripts.index_property_embeddings.SessionLocal")
def test_embedding_failure_does_not_print_exception_text(
        session_local,
        document_service_class,
        embedding_service_class,
        capsys,
):
    database = _database_with_batches([SimpleNamespace(id=7)], [])
    session_local.return_value = database
    document_service_class.return_value.build_document.return_value = "document"
    embedding_service_class.return_value.embed_document.side_effect = RuntimeError(
        SENSITIVE_VALUE
    )

    index_embeddings(batch_size=1)

    output = capsys.readouterr().out
    assert "Property 7: RuntimeError" in output
    assert SENSITIVE_VALUE not in output
    database.close.assert_called_once_with()


@patch("scripts.index_property_embeddings.EmbeddingService")
@patch("scripts.index_property_embeddings.PropertyDocumentService")
@patch("scripts.index_property_embeddings.SessionLocal")
def test_database_failure_does_not_print_exception_text(
        session_local,
        document_service_class,
        embedding_service_class,
        capsys,
):
    database = _database_with_batches([SimpleNamespace(id=8)], [])
    session_local.return_value = database
    document_service_class.return_value.build_document.return_value = "document"
    embedding_service_class.return_value.embed_document.return_value = [0.0] * 384
    database.commit.side_effect = RuntimeError(SENSITIVE_VALUE)

    index_embeddings(batch_size=1)

    output = capsys.readouterr().out
    assert "Falha ao salvar lote: RuntimeError" in output
    assert "Property 8: RuntimeError" in output
    assert SENSITIVE_VALUE not in output
    assert database.rollback.call_count == 2
    database.close.assert_called_once_with()


@patch("scripts.index_property_embeddings.parse_arguments")
@patch("scripts.index_property_embeddings.SessionLocal")
def test_main_handles_session_creation_failure_safely(
        session_local,
        parse_arguments,
        capsys,
):
    parse_arguments.return_value = SimpleNamespace(limit=None, batch_size=10)
    session_local.side_effect = RuntimeError(AUDIT_SENSITIVE_VALUE)

    try:
        main()
    except SystemExit as error:
        assert error.code == 1
    else:
        raise AssertionError("main deveria terminar com falha")

    output = capsys.readouterr()
    assert "Falha na indexação: RuntimeError" in output.out
    assert AUDIT_SENSITIVE_VALUE not in output.out
    assert AUDIT_SENSITIVE_VALUE not in output.err


@patch("scripts.index_property_embeddings.parse_arguments")
@patch("scripts.index_property_embeddings.EmbeddingService")
@patch("scripts.index_property_embeddings.SessionLocal")
def test_main_closes_session_when_embedding_service_creation_fails(
        session_local,
        embedding_service_class,
        parse_arguments,
        capsys,
):
    database = Mock()
    session_local.return_value = database
    embedding_service_class.side_effect = RuntimeError(AUDIT_SENSITIVE_VALUE)
    parse_arguments.return_value = SimpleNamespace(limit=None, batch_size=10)

    try:
        main()
    except SystemExit as error:
        assert error.code == 1
    else:
        raise AssertionError("main deveria terminar com falha")

    output = capsys.readouterr()
    assert error_type_is_safe(output.out)
    assert AUDIT_SENSITIVE_VALUE not in output.out
    assert AUDIT_SENSITIVE_VALUE not in output.err
    database.close.assert_called_once_with()


@patch("scripts.index_property_embeddings.parse_arguments")
@patch("scripts.index_property_embeddings.EmbeddingService")
@patch("scripts.index_property_embeddings.PropertyDocumentService")
@patch("scripts.index_property_embeddings.SessionLocal")
def test_main_closes_session_when_query_fails(
        session_local,
        document_service_class,
        embedding_service_class,
        parse_arguments,
        capsys,
):
    database = Mock()
    database.execute.side_effect = RuntimeError(AUDIT_SENSITIVE_VALUE)
    session_local.return_value = database
    parse_arguments.return_value = SimpleNamespace(limit=None, batch_size=10)

    try:
        main()
    except SystemExit as error:
        assert error.code == 1
    else:
        raise AssertionError("main deveria terminar com falha")

    output = capsys.readouterr()
    assert error_type_is_safe(output.out)
    assert AUDIT_SENSITIVE_VALUE not in output.out
    assert AUDIT_SENSITIVE_VALUE not in output.err
    database.close.assert_called_once_with()
    document_service_class.assert_called_once_with()
    embedding_service_class.assert_called_once_with()


def error_type_is_safe(output: str) -> bool:
    return "Falha na indexação: RuntimeError" in output

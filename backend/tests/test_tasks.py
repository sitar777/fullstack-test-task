from unittest.mock import AsyncMock, MagicMock

from tests.conftest import make_stored_file
from src.tasks import _process_uploaded_file


async def test_process_clean_file_creates_info_alert(mock_session_maker, temp_storage):
    file_item = make_stored_file(mime_type="text/plain")
    stored_path = temp_storage / file_item.stored_name
    stored_path.write_bytes(b"hello\nworld")

    _, mock_session = mock_session_maker
    mock_session.get = AsyncMock(return_value=file_item)
    mock_session.execute = AsyncMock(
        return_value=MagicMock(
            scalars=MagicMock(return_value=MagicMock(first=MagicMock(return_value=None)))
        )
    )

    await _process_uploaded_file(file_item.id)

    assert file_item.scan_status == "clean"
    assert file_item.requires_attention is False
    assert file_item.processing_status == "processed"
    assert file_item.metadata_json is not None
    mock_session.add.assert_called_once()
    added_alert = mock_session.add.call_args.args[0]
    assert added_alert.level == "info"
    mock_session.commit.assert_awaited_once()


async def test_process_suspicious_exe_creates_warning_alert(mock_session_maker, temp_storage):
    file_item = make_stored_file(
        original_name="malware.exe",
        stored_name=f"{make_stored_file().id}.exe",
        mime_type="application/octet-stream",
    )
    stored_path = temp_storage / file_item.stored_name
    stored_path.write_bytes(b"MZ")

    _, mock_session = mock_session_maker
    mock_session.get = AsyncMock(return_value=file_item)
    mock_session.execute = AsyncMock(
        return_value=MagicMock(
            scalars=MagicMock(return_value=MagicMock(first=MagicMock(return_value=None)))
        )
    )

    await _process_uploaded_file(file_item.id)

    assert file_item.scan_status == "suspicious"
    assert file_item.requires_attention is True
    assert file_item.processing_status == "processed"
    mock_session.add.assert_called_once()
    added_alert = mock_session.add.call_args.args[0]
    assert added_alert.level == "warning"
    mock_session.commit.assert_awaited_once()


async def test_process_uploaded_file_does_not_duplicate_alert_on_retry(mock_session_maker):
    file_item = make_stored_file(processing_status="processed", requires_attention=False)
    existing_alert = MagicMock()

    _, mock_session = mock_session_maker
    mock_session.get = AsyncMock(return_value=file_item)
    mock_session.execute = AsyncMock(
        return_value=MagicMock(
            scalars=MagicMock(return_value=MagicMock(first=MagicMock(return_value=existing_alert)))
        )
    )

    await _process_uploaded_file(file_item.id)

    mock_session.add.assert_not_called()
    mock_session.commit.assert_awaited_once()


async def test_process_sets_metadata_for_text_file(mock_session_maker, temp_storage):
    file_item = make_stored_file(mime_type="text/plain")
    stored_path = temp_storage / file_item.stored_name
    stored_path.write_bytes(b"line1\nline2\n")

    _, mock_session = mock_session_maker
    mock_session.get = AsyncMock(return_value=file_item)
    mock_session.execute = AsyncMock(
        return_value=MagicMock(
            scalars=MagicMock(return_value=MagicMock(first=MagicMock(return_value=None)))
        )
    )

    await _process_uploaded_file(file_item.id)

    assert file_item.metadata_json == {
        "extension": ".txt",
        "size_bytes": file_item.size,
        "mime_type": "text/plain",
        "line_count": 2,
        "char_count": len(b"line1\nline2\n"),
    }
    assert file_item.processing_status == "processed"

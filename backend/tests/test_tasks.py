from unittest.mock import AsyncMock, MagicMock, patch

from tests.conftest import make_stored_file
from src.tasks import _scan_file_for_threats, _send_file_alert


async def test_process_clean_file_creates_info_alert(mock_session_maker, temp_storage):
    file_item = make_stored_file(mime_type="text/plain", scan_status="clean")
    stored_path = temp_storage / file_item.stored_name
    stored_path.write_bytes(b"hello\nworld")

    _, mock_session = mock_session_maker
    mock_session.get = AsyncMock(return_value=file_item)
    mock_session.execute = AsyncMock(return_value=MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))))

    with patch("src.tasks.extract_file_metadata.delay") as metadata_delay:
        await _scan_file_for_threats(file_item.id)

    assert file_item.scan_status == "clean"
    assert file_item.requires_attention is False
    metadata_delay.assert_called_once_with(file_item.id)


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

    with patch("src.tasks.extract_file_metadata.delay") as metadata_delay:
        await _scan_file_for_threats(file_item.id)

    assert file_item.scan_status == "suspicious"
    assert file_item.requires_attention is True
    metadata_delay.assert_called_once_with(file_item.id)


async def test_send_file_alert_does_not_duplicate_on_retry(mock_session_maker):
    file_item = make_stored_file(processing_status="processed", requires_attention=False)
    existing_alert = MagicMock()

    _, mock_session = mock_session_maker
    mock_session.get = AsyncMock(return_value=file_item)
    mock_session.execute = AsyncMock(
        return_value=MagicMock(
            scalars=MagicMock(return_value=MagicMock(first=MagicMock(return_value=existing_alert)))
        )
    )

    await _send_file_alert(file_item.id)

    mock_session.add.assert_not_called()


async def test_process_sets_metadata_for_text_file(mock_session_maker, temp_storage):
    from src.tasks import _extract_file_metadata

    file_item = make_stored_file(mime_type="text/plain")
    stored_path = temp_storage / file_item.stored_name
    stored_path.write_bytes(b"line1\nline2\n")

    _, mock_session = mock_session_maker
    mock_session.get = AsyncMock(return_value=file_item)

    with patch("src.tasks.send_file_alert.delay") as alert_delay:
        await _extract_file_metadata(file_item.id)

    assert file_item.metadata_json == {
        "extension": ".txt",
        "size_bytes": file_item.size,
        "mime_type": "text/plain",
        "line_count": 2,
        "char_count": len(b"line1\nline2\n"),
    }
    assert file_item.processing_status == "processed"
    alert_delay.assert_called_once_with(file_item.id)

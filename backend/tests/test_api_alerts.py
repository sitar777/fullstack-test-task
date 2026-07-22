from unittest.mock import AsyncMock, MagicMock

from tests.conftest import make_alert, make_stored_file


async def test_list_alerts_returns_200(test_client, mock_session_maker):
    file_item = make_stored_file()
    alert = make_alert(file_id=file_item.id)
    _, mock_session = mock_session_maker

    result = MagicMock()
    result.scalars.return_value.all.return_value = [alert]
    mock_session.execute = AsyncMock(return_value=result)

    response = await test_client.get("/alerts")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["file_id"] == file_item.id
    assert payload[0]["level"] == "info"

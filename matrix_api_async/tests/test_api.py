from asyncio import Future
from functools import partial
from urllib.parse import quote
from unittest.mock import MagicMock, Mock, call

import pytest
import matrix_client.errors

from matrix_api_async import AsyncHTTPAPI


def client_session(json, status=200):
    client_session = MagicMock()

    class MockResponse(MagicMock):
        called = 0
        async def __aenter__(self):
            response = MagicMock()
            f = Future()
            f.set_result(json)
            response.json = Mock(return_value=f)
            response.status = self.status()
            f = Future()
            f.set_result("hello")
            response.text = Mock(return_value=f)
            return response

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

        def status(self):
            if status == 429 and self.called > 0:
                return 200
            else:
                self.called += 1
                return status


    client_session.request = MockResponse()

    return client_session

@pytest.fixture
def api():
    return partial(AsyncHTTPAPI, base_url="base_url", token="1234")


@pytest.mark.asyncio
async def test_send(api):
    api = api(client_session=client_session({}))

    response = await api._send("GET", "/createRoom")
    api.client_session.request.assert_called_once_with("GET",
                                                       "base_url/_matrix/client/r0/createRoom",
                                                       data="{}",
                                                       headers={"Content-Type": "application/json"},
                                                       params={"access_token": "1234"})


@pytest.mark.asyncio
async def test_send_429(api):
    api = api(client_session=client_session({}, status=429))

    response = await api._send("GET", "/createRoom")
    call429 = call("GET",
                   "base_url/_matrix/client/r0/createRoom",
                   data="{}",
                   headers={"Content-Type": "application/json"},
                   params={"access_token": "1234"})

    # If we 429 we should call request twice with the same parameters
    api.client_session.request.assert_has_calls([call429, call429])



@pytest.mark.parametrize("json", [{"error": '{"retry_after_ms": 10}'},
                                  {"error": {"retry_after_ms": 10}},
                                  {"retry_after_ms": 10}])
@pytest.mark.asyncio
async def test_send_429_timeout(api, json):
    api = api(client_session=client_session(json, status=429))

    response = await api._send("GET", "/createRoom")

    call429 = call("GET",
                   "base_url/_matrix/client/r0/createRoom",
                   data="{}",
                   headers={"Content-Type": "application/json"},
                   params={"access_token": "1234"})

    # If we 429 we should call request twice with the same parameters
    api.client_session.request.assert_has_calls([call429, call429])


@pytest.mark.asyncio
async def test_send_404(api):
    api = api(client_session=client_session({}, status=404))

    with pytest.raises(matrix_client.errors.MatrixRequestError) as exc:
        response = await api._send("GET", "/createRoom")
        assert exc.status == 404
        assert exc.content == "hello"


@pytest.mark.asyncio
async def test_get_displayname(api):
    api = api(client_session=client_session({"displayname": "African swallow"}))
    mxid = "@user:test"
    displayname = await api.get_display_name(mxid)
    assert displayname == "African swallow"

    api.client_session.request.assert_called_once_with("GET",
                                                       f"base_url/_matrix/client/r0/profile/{mxid}/displayname",
                                                       data="{}",
                                                       headers={"Content-Type": "application/json"},
                                                       params={"access_token": "1234"})


@pytest.mark.asyncio
async def test_set_displayname(api):
    api = api(client_session=client_session({}))
    mxid = "@user:test"
    await api.set_display_name(mxid, "African swallow")

    api.client_session.request.assert_called_once_with("PUT",
                                                       f"base_url/_matrix/client/r0/profile/{mxid}/displayname",
                                                       data='{"displayname": "African swallow"}',
                                                       headers={"Content-Type": "application/json"},
                                                       params={"access_token": "1234"})


@pytest.mark.asyncio
async def test_get_avatar_url(api):
    api = api(client_session=client_session({"avatar_url": "mxc://hello"}))
    mxid = "@user:test"
    url = await api.get_avatar_url(mxid)
    assert url == "mxc://hello"

    api.client_session.request.assert_called_once_with("GET",
                                                       f"base_url/_matrix/client/r0/profile/{mxid}/avatar_url",
                                                       data="{}",
                                                       headers={"Content-Type": "application/json"},
                                                       params={"access_token": "1234"})


@pytest.mark.asyncio
async def test_get_room_id(api):
    api = api(client_session=client_session({"room_id": "aroomid"}))
    mxid = "@user:test"
    room_alias = "#test:test"
    aid = await api.get_room_id(room_alias)
    assert aid == "aroomid"

    api.client_session.request.assert_called_once_with("GET",
                                                       f"base_url/_matrix/client/r0/directory/room/{quote(room_alias)}",
                                                       data="{}",
                                                       headers={"Content-Type": "application/json"},
                                                       params={"access_token": "1234"})


@pytest.mark.asyncio
async def test_get_room_displayname(api):
    mxid = "@user:test"
    api = api(client_session=client_session({"chunk":
                                             [{"sender": mxid, "content": {"displayname": "African swallow"}}]}))
    room_alias = "#test:test"
    displayname = await api.get_room_displayname("arromid", mxid)
    assert displayname == "African swallow"

    api.client_session.request.assert_called_once_with("GET",
                                                       f"base_url/_matrix/client/r0/rooms/arromid/members",
                                                       data="{}",
                                                       headers={"Content-Type": "application/json"},
                                                       params={"access_token": "1234"})


# Test the wrapping of a sync method
@pytest.mark.asyncio
async def test_sync_wrap(api):
    api = api(client_session=client_session({}))
    roomid = "!ldjaslkdja:test"
    eventid = "$alskdjsalkdjal:test"
    displayname = await api.get_event_in_room(roomid, eventid)

    api.client_session.request.assert_called_once_with("GET",
                                                       f"base_url/_matrix/client/r0/rooms/{roomid}/event/{eventid}",
                                                       data="{}",
                                                       headers={"Content-Type": "application/json"},
                                                       params={"access_token": "1234"})

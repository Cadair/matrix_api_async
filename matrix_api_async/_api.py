"""
A slightly modified version of the sync API class to make things a little neater.

All the non-asyncio stuff should go in here.
"""
from matrix_client.api import MatrixHttpApi as _MatrixHttpApi

__all__ = ["MatrixHttpApi"]


MATRIX_V2_API_PATH = "/_matrix/client/r0"


class MatrixHttpApi(_MatrixHttpApi):
    def _prepare_send(self, method, content, query_params, headers, path, api_path):
        """
        Process the arguments to the _send method.

        This is factored out of _send as it is shared by the asyncio class.
        """
        method = method.upper()
        if method not in ["GET", "PUT", "DELETE", "POST"]:
            raise MatrixError("Unsupported HTTP method: %s" % method)

        if not content:
            content = {}
        if not query_params:
            query_params = {}
        if not headers:
            headers = {}

        if "Content-Type" not in headers:
            headers["Content-Type"] = "application/json"

        query_params["access_token"] = self.token
        if self.identity:
            query_params["user_id"] = self.identity

        endpoint = self.base_url + api_path + path

        if headers["Content-Type"] == "application/json" and content is not None:
            content = json.dumps(content)

        return content, query_params, headers, endpoint

    def _get_waittime(self, responsejson):
        """
        Read the response from a 429 and return a time in seconds to wait.

        This is factored out of _send as it is shared by the asyncio class.
        """
        try:
            waittime = responsejson['retry_after_ms'] / 1000
        except KeyError:
            try:
                errordata = json.loads(responsejson['error'])
                waittime = errordata['retry_after_ms'] / 1000
            except KeyError:
                waittime = self.default_429_wait_ms / 1000
        finally:
            return waittime

    def _send(self, method, path, content=None, query_params=None, headers=None,
              api_path=MATRIX_V2_API_PATH):

        args = self._prepare_send(method, content, query_params, headers, path, api_path)
        content, query_params, headers, endpoint = args

        while True:
            try:
                response = self.session.request(
                    method, endpoint,
                    params=query_params,
                    data=content,
                    headers=headers,
                    verify=self.validate_cert
                )
            except RequestException as e:
                raise MatrixHttpLibError(e, method, endpoint)

            if response.status_code == 429:
                sleep(self._get_waittime(response.json()))
            else:
                break

        if response.status_code < 200 or response.status_code >= 300:
            raise MatrixRequestError(
                code=response.status_code, content=response.text
            )

        return response.json()

    def get_event_in_room(self, room_id, event_id):
        """
        Get a single event based on roomId/eventId.

        You must have permission to retrieve this event e.g. by being a member
        in the room for this event.
        """
        return self._send("GET", "/rooms/{}/event/{}".format(room_id, event_id))

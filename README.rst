matrix_api_async
================

An asyncio wrapper of `matrix_client.api`.

This is based on the work in https://github.com/matrix-org/matrix-python-sdk/pull/168

Usage
-----

::

  import aiohttp
  from matrix_api_async import AsyncHTTPAPI

    async def main():
        async with aiohttp.ClientSession() as session:
            mapi = AsyncHTTPAPI("http://matrix.org", session)
            resp = await mapi.get_room_id("#matrix:matrix.org")
            print(resp)


    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())


Installation
------------

`pip install matrix_api_async`

Requirements
^^^^^^^^^^^^

* matrix_client
* aiohttp (Could potentially be used with other libraries)

Compatibility
-------------

Python 3.5+

Licence
-------

MIT

Authors
-------

`matrix_api_async` was written by `Stuart Mumford <stuart@cadair.com>`_.

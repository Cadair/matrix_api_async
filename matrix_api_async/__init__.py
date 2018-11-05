"""matrix_api_async - An asyncio wrapper of matrix_client.api"""

__version__ = '0.1.0'
__author__ = 'Stuart Mumford <stuart@cadair.com>'

from .api_asyncio import AsyncHTTPAPI

__all__ = ["AsyncHTTPAPI"]

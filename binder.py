import asyncio

from aiofiles import open as _open
from aiohttp import ClientSession, ClientTimeout
from os import remove
from os.path import join


class Binder:

    def __init__(self):
        self.timeout = ClientTimeout(50000)

    async def get_and_save_photo(self, name, url):
        async with ClientSession() as session:
            async with session.get(url,
                                   timeout=self.timeout) as resp:
                content = await resp.read()
        if isinstance(content, bytes):
            async with _open(join('cache/', f'{name}.png'), 'wb') as file:
                await file.write(content)
                await file.close()
        return join('cache/', f'{name}.png')

    async def delete_photo(self, name):
        remove(join('cache/', f'{name}.png'))

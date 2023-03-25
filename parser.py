import asyncio

from bs4 import BeautifulSoup as bs
from aiohttp import ClientSession, ClientTimeout
from fake_useragent import UserAgent
from urllib.parse import quote

from logger import Async_logging
from SecondaryPlugins.errors import ParserParsError, ConnectionErrorFailed


class Connector():

    def __init__(self):
        self.search_url = "https://povar.ru/xmlsearch?query="
        self.default_url = "https://povar.ru/"
        self.timeout = ClientTimeout(50000)
        self.agent = UserAgent().random
        self.headers = {"user-agent": self.agent}

    async def _standart_request(self, url):
        async with ClientSession() as session:
            async with session.get(url,
                                   headers=self.headers,
                                   timeout=self.timeout) as resp:
                response = await resp.read()
        return response

    async def _standart_request_to_main_page(self):
        response = await self._standart_request(self.default_url)
        return response

    async def _create_object(self, page: bytes):
        return bs(page.decode(), 'html.parser')

    async def search(self, q):
        response = await self._standart_request(f"{self.search_url}{quote(q)}")
        soup_object = await self._create_object(response)
        return soup_object

    async def get_recipe(self, url):
        response = await self._standart_request(f'{self.default_url}{url}')
        soup_object = await self._create_object(response)
        return soup_object

    async def get_new_recipe(self):
        response = await self._standart_request_to_main_page()
        soup_object = await self._create_object(response)
        list_of_new_recipe = soup_object.find(
            'div', class_='recipe_list').find_all('div', class_='recipe')
        return list_of_new_recipe

    async def get_standart_menu(self):
        response = await self._standart_request_to_main_page()
        soup_object = await self._create_object(response)
        menu = soup_object.find('div', class_='floatingMenu')
        head = menu.find_all('a', class_='fmHead')
        return head

    async def get_menu_object(self, index: int = 0):
        menu = await self.get_standart_menu()
        #print(self.default_url + menu[index - 1]['href'][1:])
        no_pars_page = await self._standart_request(self.default_url + menu[index - 1]['href'][1:])
        page = await self._create_object(no_pars_page)
        headers = page.find_all('div', class_='suite')
        return headers

    async def get_menu_subobject(self, index0: int = 0, index1: int = 0):
        raw_menu = await self.get_menu_object(index=index0)
        menu = list(map(lambda x: x.find('a'), raw_menu))
        no_pars_page = await self._standart_request(self.default_url + menu[index1 - 1]['href'][1:])
        page = await self._create_object(no_pars_page)
        recipes = page.find_all('div', class_='recipe')
        return list(map(list, [
            map(lambda x: x.find('a', class_='listRecipieTitle'), recipes),
            map(lambda x: x.find('span', class_='rate').text, recipes),
            map(lambda x: x.find('img')['src'], recipes),
            map(lambda x: x.find('p', class_='txt').text, recipes)
        ]))

    async def pars_recipe(self, url: str = ''):
        raw_page = await self._standart_request(self.default_url + url[1:])
        page = await self._create_object(raw_page)
        parts = page.find_all('a', class_='stepphotos')
        return list(map(list, [
                        map(lambda x: x['title'], parts),
                        map(lambda x: x['href'], parts)
                        ]
                        ))

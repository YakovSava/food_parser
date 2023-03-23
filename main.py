import asyncio
import bs4

from aiogram import Bot, Dispatcher, executor
from aiogram.types import Message
from os.path import join

from parser import Connector
from binder import Binder
from config import bot_token

from pprint import pprint

connect = Connector()
binder = Binder()
bot = Bot(bot_token)
dp = Dispatcher(bot)


@dp.message_handler(commands=['start', 'help'])
async def start_help(message: Message):
    await message.answer('Напиши мне "Рецепт (блюдо)" и я покажу тебе список всех рецептов\nКак только ты посмотришь все рецепты ты можешь ввести "Рецепт (блюдо) (номер рецепта) что-бы я отобразил именно этот рецепт!"')


@dp.message_handler(commands=['recipe'])
async def get_recipe(message: Message):
    *_, num = message['text'].split()
    try:
        number_of_recipe = int(num)
        question = message['text'][8:-len(str(number_of_recipe)) - 1]
        response = await connect.search(question)
        all_recipes = response.find_all("div", class_="recipe")
        link = all_recipes[number_of_recipe - 1].find("a")["href"]
        html_page = await connect.get_recipe(link)
        recipe_parts = html_page.find_all(
            'div', class_='detailed_step_description_big')
        recipe_parts_photo = html_page.find_all('a', class_='stepphotos')
        for rp_index in range(0, len(recipe_parts)):  # rp_index - recipe part index
            img = recipe_parts_photo[rp_index].img['src']
            text = recipe_parts[rp_index].text
            await binder.get_and_save_photo(f"{message['from']['id']}_{rp_index}", img)
            await bot.send_photo(chat_id=message['from']['id'],
                                 photo=open(
                                     join('cache/', f"{message['from']['id']}_{rp_index}.png"), 'rb'),
                                 caption=str(text))
            await binder.delete_photo(f"{message['from']['id']}_{rp_index}")
    except ValueError:
        question = message['text'][8:]
        response = await connect.search(question)
        all_recipes = response.find_all("div", class_="recipe")
        images = []
        counter = 0
        for recipe in all_recipes:
            link = recipe.find("a")["href"]
            rate = recipe.find("span", class_="rate").text
            img = recipe.find("img")["src"]
            await binder.get_and_save_photo(f"{message['from']['id']}_{counter}", img)
            title = recipe.find("a").text
            description = recipe.find("p").text
            await bot.send_photo(chat_id=message['from']['id'],
                                 photo=open(
                                     join('cache/', f"{message['from']['id']}_{counter}.png"), 'rb'),
                                 caption=f'''{"-"*45}
Рецепт номер {counter + 1}
{"-"*45}
=== {title} ===
Оценка: {rate}
Описание:
{description[:-8]}
{"-"*45}''')
            await binder.delete_photo(f"{message['from']['id']}_{counter}")
            counter += 1


@dp.message_handler(commands=['new'])
async def new_recipes(message: Message):
    resp = await connect.get_new_recipe()
    try:
        *_, num = message['text'].split()
        nr_index = int(num)  # new recipe index
        link = resp[nr_index - 1].find("a")["href"]
        html_page = await connect.get_recipe(link)
        recipe_parts = html_page.find_all(
            'div', class_='detailed_step_description_big')
        recipe_parts_photo = html_page.find_all('a', class_='stepphotos')
        for rp_index in range(0, len(recipe_parts)):
            img = recipe_parts_photo[rp_index].img['src']
            text = recipe_parts[rp_index].text
            await binder.get_and_save_photo(f"{message['from']['id']}_{rp_index}", img)
            await bot.send_photo(chat_id=message['from']['id'],
                                 photo=open(
                                     join('cache/', f"{message['from']['id']}_{rp_index}.png"), 'rb'),
                                 caption=text)
            await binder.delete_photo(f"{message['from']['id']}_{rp_index}")
    except ValueError:
        counter = 0
        for popular in resp:
            title = popular.find('a', class_='listRecipieTitle').text
            description = popular.find('p', class_='txt').text
            rate = popular.find('span', class_='rate').text
            img_url = popular.find('img')['src']
            await binder.get_and_save_photo(f"{message['from']['id']}_{counter}", img_url)
            await bot.send_photo(chat_id=message['from']['id'],
                                 photo=open(
                                     join('cache/', f"{message['from']['id']}_{counter}.png"), 'rb'),
                                 caption=f'''{"-"*45}
Новый рецепт номер {counter + 1}
{"-"*45}
=== {title} ===
Оценка: {rate}
Описание:
{description[:-8]}
{"-"*45}''')
            await binder.delete_photo(f"{message['from']['id']}_{counter}")
            counter += 1


@dp.message_handler(commands=['menu'])
async def menu(message: Message):
    standart_menu = await connect.get_standart_menu()
    message_list = message['text'].split()
    message_list.extend(['null' for _ in range(5)])
    if not message_list[1].isdigit():
        text = f'{"*" * 20} Главное меню {"*" * 20}\n'
        counter = 0
        for menu_position in standart_menu:
            text += f'{counter + 1}: {menu_position.text}\n'
            counter += 1
        text += f'\nЕсли хотите получить подробностей по поределённой позиции, пропишите /menu (номер позиции)'
        await message.answer(text)
    else:
        menu_object = await connect.get_menu_object(int(message_list[1]))
        if not message_list[2].isdigit():
            text = f'{"-" * 20} Все возможные рецепты {"-" * 20}\n'
            counter = 0
            for menu_position_position in menu_object:
                text += f'{counter + 1}: {menu_position_position.text}\n'
                counter += 1
            text += '\nЧто бы продолжить изучать разнообразные варианты рецептов, введите "/menu (Номер позиции) (Номер позиции)"'
            await message.answer(text)
        else:
            menu_subobject = await connect.get_menu_subobject(int(message_list[1]), int(message_list[2]))
            if not message_list[3].isdigit():
                for index in range(len(menu_subobject[0])):
                    photo_path = await binder.get_and_save_photo(f'{message["from"]["id"]}_{index}', menu_subobject[2][index])
                    await bot.send_photo(
                        chat_id=message['from']['id'],
                        photo=open(photo_path, 'rb'),
                        caption=f'''{"-" * 20} {menu_subobject[0][index].text} {"-" * 20}
Оценка: {menu_subobject[1][index]}
Описание: {menu_subobject[3][index][:-8]}
{"-" * 50}''')
                    await binder.delete_photo(f'{message["from"]["id"]}_{index}')
                await message.answer('Что бы получить определённый рецепт введите "/menu (Номер позиции) (Номер позиции) (Номер позиции)"')
            else:
                recipe_parts = await connect.pars_recipe(menu_subobject[0][int(message_list[3])]['href'])
                for index in range(len(recipe_parts[0])):
                    photo_path = await binder.get_and_save_photo(f'{message["from"]["id"]}_{index}', recipe_parts[1][index])
                    await bot.send_photo(
                        chat_id=message['from']['id'],
                        photo=open(photo_path, 'rb'),
                        caption=f'{recipe_parts[0][index]}'
                    )
                    await binder.delete_photo(f'{message["from"]["id"]}_{index}')


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)

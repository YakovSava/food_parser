from aiofiles import open as _open  # Импортируем асинхронное открытий файлов
from os import remove  # Импортируем удаление

from SecondaryPlugins.errors import LoggingBeginError, LoggingError, LoggingHashError


class Async_logging():  # Обьявляем класс

    def __init__(self):  # Инициализация
        self.name = "log_file.log"  # Название файла (изменяемо)
        self.version = "1.0"  # Версия (неизменяемо)
        self.hash = False  # Хэшировать или нет (изменяемо)
        self.hashing = ""  # Хэш (сам изменяется)
        self.is_begin = False

    async def set_file_name(self, name: str):  # Изменение названия файла
        self.name = name

    async def set_hash(self, parameter: bool):  # Изменяем параметр хэширования
        if self.hash != parameter:
            self.hash = parameter
        else:
            raise LoggingHashError(f'"Hash " already {parameter}')

    async def delete(self):  # Ужалить файл с логом
        remove(self.name)

    async def remove_hash(self):  # Удаляем хэш
        self.hash = ""

    async def begin(self):  # Начало лога
        async with _open(self.name, "w") as log:
            await log.write("")  # Стираем всё записываем ничего
            await log.close()
        self.is_begin = True

    async def record(self, record):  # Запись
        if self.is_begin:
            if self.hash:
                self.hashing += f"{record} -- "  # В хэш запись идёт такая
            else:
                async with _open(self.name, "a") as log:  # Вне хэша запись такая
                    await log.write(f"{record}\n")
                    await log.close()
        else:
            raise LoggingBeginError("Log not started")

    async def error(self, error, msg=None):  # Ошибка
        if self.is_begin:
            if self.hash:  # Если хэшируется
                self.hashing += f"Error!\n{error}\nComment: {msg} -- "
            else:
                async with _open(self.name, "a") as log:
                    # Записываем
                    await log.write(f"Error!\n{error}\nComment: {msg}")
                    await log.close()
        else:
            raise LoggingBeginError("Log not started")

    async def hash_and_remove(self, parameter: bool):  # Хэшируем файл
        if parameter:
            self.hash = parameter
            async with _open(self.name, "r") as log_end:
                file = await log_end.readlines()
            for string_ in file:  # Пробегаемся циклом по записи хэша
                await self.record(string_)
            await self.delete()  # После записи в хэш ужаляем файл

    async def hash_in_file(self):  # Записываем хэш
        async with _open(self.name, "w") as log:
            for hash_msg in self.hashing:  # Пробегаемся по хэшу циклом
                await log.write(hash_msg)
            await log.close()  # Закрываем файл

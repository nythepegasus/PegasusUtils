import sqlite3
import typing
from inspect import signature
from typing import TypeVar
from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass

import aiosqlite


SQLI_TYPES = ('NULL', 'BLOB', 'TEXT', 'REAL', 'INTEGER',)
PY_TO_SQLI = {None: 'NULL', bytes: 'BLOB', str: 'TEXT', float: 'REAL', int: 'INTEGER'}


class SQLiteException(Exception):
    def __init__(self, data, message: str = "A SQLite error has occurred"):
        super().__init__(message)
        self.data = data
        self.message = message


class SQLiteConstraint:
    def __init__(self, name: str):
        self.name = name

    @property
    def schema(self):
        raise NotImplementedError("This class is not meant to be used directly, please use a subclass")


class PrimaryKey(SQLiteConstraint):
    @property
    def schema(self):
        return " PRIMARY KEY"


class ForeignKey(SQLiteConstraint):
    def __init__(self, name: str, rtable, rvalue):
        self.name = name
        self.rtable = rtable
        self.rvalue = rvalue

    @property
    def schema(self):
        return f" FOREIGN KEY({self.name}) REFERENCES {self.rtable}({self.rvalue})"


class SQLiteKey:
    def __init__(self, name: str, value: None | bytes | str | float | int, \
                 constraints = None):
        self._type = type(value)
        if self._type not in [None, bytes, str, float, int]:
            raise SQLiteException(value, f"{value} does not appear to be a proper SQLite type")
        self.name = name
        self.value = value
        self.constraints = constraints

    @property
    def schema(self):
        return f"{self.name} {PY_TO_SQLI[self._type]}"


class BasicSQLiteDBType:
    def __new__(cls, *args, **kwargs):
        cls.INSTANCES = [] if getattr(cls, 'INSTANCES', None) is None else cls.INSTANCES
        instance = super().__new__(cls)
        instance.id = len(cls.INSTANCES)
        cls.INSTANCES.append(instance)

        try:
            params = list(cls.__dict__['__annotations__'].keys())
        except KeyError:
            params = list(signature(cls.__init__).parameters.items())[1:]
        if len(params) != len(args):
            raise Exception("?")
        for i in range(len(params)):
            setattr(instance, params[i][0], args[i])

        return instance

    def convert(self, data: typing.Any):
        ret = (SQLI_TYPES[0], None)
        if isinstance(data, bytes):
            ret = (SQLI_TYPES[1], bytes(data))
        elif isinstance(data, str):
            ret = (SQLI_TYPES[2], str(data))
        elif isinstance(data, float):
            ret = (SQLI_TYPES[3], float(data))
        elif isinstance(data, int):
            ret = (SQLI_TYPES[4], int(data))

        return ret

    @property
    def table_query(self):
        query = f"CREATE TABLE IF NOT EXISTS {self.__class__.__name__.lower()} "
        query_types = "("
        for index, (item, value) in enumerate(self.__dict__.items()):
            if isinstance(value, list) or value is None:
                continue
            query_types += f"{item} {self.convert(value)[0]}"
            if item == 'id':
                query_types += " PRIMARY KEY, "
            else:
                query_types += ", "

        query += query_types[:-2] + ")"
        return query

    def __str__(self):
        ret = f"{self.__class__.__name__}("
        for item, value in self.__dict__.items():
            ret += "{item}={value}, "
        ret = ret[:-2] + ")"
        return ret

    def __repr__(self):
        ret = f"{self.__class__.__name__}("
        for item, value in self.__dict__.items():
            ret += f"{item}={value}, "
        ret = ret[:-2] + ")"
        return ret

    def _insert(self, instance: bool = False):
        keys = list(self.__dict__.keys())
        query = f"INSERT INTO {self.__class__.__name__.lower()} "
        query_keys = "("
        query_vals = "VALUES ("
        for key in keys:
            value = getattr(self, key)
            if not isinstance(value, list):
                query_keys += f"{key}, "
                if isinstance(value, str):
                    value = f"'{value}'"
                query_vals += "?, " if not instance else f"{value}, "

        query += query_keys[:-2] + ") "
        query += query_vals[:-2] + ")"

        return query

    @property
    def insert_query(self):
        return self._insert()
    
    @property
    def insert(self):
        return self._insert(True)

    @property
    def values(self):
        return [f"'{v}'" if isinstance(v, str) else v for v in self.__dict__.values() if not isinstance(v, list) and v is not None]

    @property
    def select(self):
        print(list(self.__dict__.keys()))
        return

class Test(BasicSQLiteDBType):
    def __init__(self, name: str, age: int):
        self.name = name
        self.age = age + 1
        print(self.id)
        print(self.values)

class Buh(BasicSQLiteDBType):
    money: float
    city: str
    country: str

t = Test('ny', 22)
b = Test('Buh', 69)
c = Buh(20.34, 'Indianapolis', 'Indiana')
v = Buh(1337.0, 'South Bend', 'Indiana')

class SQLiteDBManager(ABC):
    def __init__(self, dbname):
        self.dbname = dbname

    @property
    @abstractmethod
    def conn(self):
        raise NotImplementedError()

    @abstractmethod
    def initdb(self):
        raise NotImplementedError()

    @abstractmethod
    async def ainitdb(self):
        raise NotImplementedError()

    def __await__(self):
        return self.ainitdb().__await__()

    def _insert(self, query: str, data: tuple[typing.Any]) -> bool:
        if not sqlite3.complete_statement(query):
            raise sqlite3.DataError("Incomplete query")
        self.conn.execute(query, data)

    def _insert_many(self, query: str, data: list[tuple[typing.Any]]) -> bool:
        pass

from dataclasses import dataclass

SQLI_TYPES = ('NULL', 'BLOB', 'TEXT', 'REAL', 'INTEGER',)
PY_TO_SQLI = {None: 'NULL', bytes: 'BLOB', str: 'TEXT', float: 'REAL', int: 'INTEGER'}

# PK(U(NN(str)))

class C:
    def __init__(self, typ):
        self.type = typ

    def __repr__(self):
        print(f"{self.__class__.__name__}({self.type})")
        if getattr(self.type, 'type', 1) == 1:
            return f"{self.__class__.__name__}({PY_TO_SQLI[self.type]})"
        else:
            return f"{self.__class__.__name__}({self.type})"

    @property
    def _type(self):
        typ = self
        while getattr(typ, 'type', 1) != 1:
            typ = typ.type

        return PY_TO_SQLI[typ]

    @property
    def schema(self):
        cons = []
        typ = self
        while getattr(typ, 'type', 1) != 1:
            cons.append(getattr(typ, '_schema', ''))
            typ = typ.type
        ret = f" {self._type}"
        if " PRIMARY KEY" in cons:
            ret += " PRIMARY KEY"
        if " UNIQUE" in cons:
            ret += " UNIQUE"
        if " NULL" in cons:
            if "NOT NULL" in cons:
                raise Exception("??")
            ret += " NULL"
        if " NOT NULL" in cons:
            if "NULL" in cons:
                raise Exception("??")
            ret += " NOT NULL"
        if "FOREIGN KEY" in getattr(self, '_schema', ''):
            ret += ",\n"
            ret += self._schema
        return ret


class PK(C):
    @property
    def _schema(self):
        return " PRIMARY KEY"


class FK(C):
    def __init__(self, typ, table_reference, table_value: str):
        super().__init__(typ)
        self.table_reference = table_reference
        self.table_value = table_value

    @property
    def _schema(self):
        return f"FOREIGN KEY({{}}) REFERENCES {self.table_reference.__name__.lower()}({self.table_value})"


class NN(C):
    @property
    def _schema(self):
        return f" NOT NULL"


class N(C):
    @property
    def _schema(self):
        return f" NULL"


class U(C):
    @property
    def _schema(self):
        return f" UNIQUE"


class D(C):
    def __init__(self, typ, value):
        self.type = typ
        self.value = value

    @property
    def _schema(self):
        return f"DEFAULT {self.value}"


class T:
    def __init__(self, *args, **kwargs):
        if len(self.__annotations__) >= len(args):
            for i, key in enumerate(self.__annotations__.keys()):
                if i > len(args) - 1:
                    break
                # print(f"{key} => {args[i]} -- {self.__annotations__[key]}")
                setattr(self, key, args[i])
        if len(self.__annotations__) == len(args) + len(kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
        else:
            if 'gimme_schema' in kwargs:
                for i, key in enumerate(self.__annotations__.keys()):
                    setattr(self, key, None)
            else:
                raise Exception("Incorrect number of arguments")

    @property
    def schema(self):
        schema = f"CREATE TABLE IF NOT EXISTS {self.__class__.__name__.lower()} (\n"
        for name, con in self.__annotations__.items():
            schema += f"{name}"
            if isinstance(con, C):
                if isinstance(con, FK):
                    schema = con.table_reference(gimme_schema=True).schema + "\n" + schema
                schema += f"{con.schema.format(name)}"
            else:
                schema += f" {PY_TO_SQLI[con]}"
            if list(self.__annotations__).index(name) != (len(self.__annotations__) - 1):
                schema += ',\n'
        schema += "\n);"
        return schema


class Server(T):
    id: PK(N(U(str)))
    name: str


class User(T):
    id: PK(int)
    name: U(NN(str))
    server: FK(U(NN(int)), Server, 'id')


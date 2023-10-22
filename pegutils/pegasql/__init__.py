from dataclasses import dataclass

SQLI_TYPES = ('NULL', 'BLOB', 'TEXT', 'REAL', 'INTEGER',)
PY_TO_SQLI = {None: 'NULL', bytes: 'BLOB', str: 'TEXT', float: 'REAL', int: 'INTEGER'}

# PK(U(NN(str)))

class C:
    def __init__(self, t):
        self.type = t

    def __repr__(self):
        # print(f"{self.__class__.__name__}({self.type})")
        if self.type in PY_TO_SQLI:
            return f"{self.__class__.__name__}({self._type})"
        else:
            return f"{self.__class__.__name__}({self.type})"

    @property
    def _type(self):
        if self.type in PY_TO_SQLI:
            return PY_TO_SQLI[self.type]
        else:
            check = self.type
            while check.type not in PY_TO_SQLI:
                check = check.type
            return PY_TO_SQLI[check.type]

    @property
    def schema(self):
        cons = []
        constraint = self.type
        while constraint.type not in PY_TO_SQLI:
            cons.append(constraint._schema)
            constraint = constraint.type
        cons.append(constraint._schema)
        ret = self._schema

        if " PRIMARY KEY" in cons:
            ret += " PRIMARY KEY"

        if " UNIQUE" in cons:
            ret += " UNIQUE"
        
        if " NULL" in cons:
            ret += " NULL"
        if " NOT NULL" in cons:
            ret += " NOT NULL"
        if " NOT NULL" in cons and " NULL" in cons:
            raise Exception("??")

        if "FOREIGN KEY" in getattr(self, '_schema', ''):
            ret += ",\n"
            ret += self._schema
        return ret

    @property
    def _schema(self):
        return f" {self._type}"


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


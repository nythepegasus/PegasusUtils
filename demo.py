# New demo ideas
from pegaSQL import T, DBM


class Server(T):
    id: int # This will make id the Primary Key by default, use _id to suppress (NOTE: you will still access self._id)
    name: ('U', str) # Most attributes are 'NOT NULL' by default, so here we add U to add Unique constraint
    members: int = 0 # This is the same as using a DEFAULT constraint, it also is NOT NULL
    verified: ('N', bool) # bool is not a SQLite type, so pegaSQL will use INT instead, also N marks it as 'NULL'able


class User(T):
    id: int
    name: str
    joined: str
    # Here's some pegaSQL magic sauce! Since we passed it another Table, it'll create the FOREIGN KEY for us!
    # Obviously this is TERRIBLE SQL, but for demonstration it's perfectly fine
    # 
    # Passing the custom Table object by itself defaults to 'id'
    # Accessing this after DBM is initialized will result in the Server object instance being returned, see further below
    server: Server

print(Server.schema)
# CREATE TABLE IF NOT EXISTS server (
#     id INT PRIMARY KEY,
#     name TEXT UNIQUE NOT NULL,
#     members INT DEFAULT 0 NOT NULL,
#     verified INT
# );
print(User.schema)
# CREATE TABLE IF NOT EXISTS user (
#     id INT PRIMARY KEY,
#     name TEXT NOT NULL,
#     joined TEXT NOT NULL,
#     server INT NOT NULL,
#     FOREIGN KEY (server) REFERENCES server(id)
# );

s = Server(0, "ny's Palace")
print(s)
# Server(0, "ny's Palace", 0)
print(s.insert) # pegaSQL magic sauce
# INSERT INTO server VALUES (0, "ny's Palace", 0);
u = User(0, 'ny', 'now', 0) # Here we can either pass the Server instance we want or its actual 'id'
print(u)
# User(0, 'ny', 'now', 0) # will show 0 if passed 0, we will see later how to fix
print(u.insert)
# INSERT INTO user VALUES (0, 'ny', 'now', 0);

db = DBM([Server, User])
# pegaSQL magic sauce, uses sqlite3 under the hood to create all your schema, and now your objects have super powers!

# Imagine you ran the insertions above already
u = User.get(id=0) # Bam
print(u)
# User(0, 'ny', 'now', Server(0, "ny's Palace", 0)) # this `u` object will always show/have the Server instance it's related to
# That behavior can be toggled off to save db calls, as the DBM has to cache each object reference (obviously)
# If you toggle the behavior, it will result in the same results as above as well as 1 less db call
# Otherwise, you can do cool stuff like this:
s = u.server
print(s)
# Server(0, "ny's Palace", 0)

# Old demo updated with new ideas
from pegasql import PegaSQLiteException, T

class Requests(T):
    time: ('PK', str)
    agent: ('PK', str)
    client: ('PK', str)
    status: int
    url: ('N', str)

"""
-- Above should create the following table schema
CREATE TABLE IF NOT EXISTS requests (
    time TEXT NOT NULL,
    agent TEXT,
    client TEXT,
    status INT NOT NULL,
    url TEXT,
    PRIMARY KEY (time, agent, client)
);
"""

class Server(T):
    id: int
    name: str


class User(T):
    id: int
    name: ('U', str)
    server: Server


class Message(T):
    id: int
    user: User
    value: str = ''

"""
-- Above should result in these table schemas
CREATE TABLE IF NOT EXISTS server (
    id INT PRIMARY KEY,
    name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS user (
    id INT PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    server INT,
    FOREIGN KEY server REFERENCES server(id)
);

CREATE TABLE IF NOT EXISTS message (
    id INT PRIMARY KEY,
    user INT,
    value TEXT DEFAULT '' NOT NULL,
    FOREIGN KEY user REFERENCES user(id)
);
"""

try:
    class Fails(T):
        id: ('PKN', int)
except PegaSQLiteException as e:
    print(e.message)


class Succeeds(T):
    id: ('PKN', str)

"""
-- The following SQLite would be invalid
CREATE TABLE IF NOT EXISTS fails (
    id INT PRIMARY KEY NULL,
);
PegaSQLiteException: Fails: `id` INT PRIMARY KEY cannot be NULL

-- Unsure of the actual usecases, but 
-- non-INT columns can be PRIMARY KEY NULL
CREATE TABLE IF NOT EXISTS succeeds (
    id TEXT PRIMARY KEY NULL,
);
"""

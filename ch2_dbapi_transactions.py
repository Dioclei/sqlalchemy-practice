from sqlalchemy import text
from sqlalchemy.orm import Session

from ch1_engine import engine

# transactions are not committed automatically, this will rollback
with engine.connect() as conn:
    result = conn.execute(text("select 'hello world'"))
    print(result.all())

# use "commit as you go" or "begin once" patterns to commit transactions
# "commit as you go"
with engine.connect() as conn:
    conn.execute(text("CREATE TABLE some_table (x int, y int)"))
    conn.execute(
        text("INSERT INTO some_table (x, y) VALUES (:x, :y)"),
        [{"x": 1, "y": 1}, {"x": 2, "y": 4}],
    )
    conn.commit()

# "begin once"
with engine.begin() as conn:
    conn.execute(
        text("INSERT INTO some_table (x, y) VALUES (:x, :y)"),
        [{"x": 6, "y": 8}, {"x": 9, "y": 10}],
    )

# fetching rows
with engine.connect() as conn:
    result = conn.execute(text("SELECT x, y FROM some_table"))

    # Result is an iterator which outputs Row objects
    # observe that for the following two for loops, only 1 outputs stuff
    # because Result is acts like a iterator / (database cursor) it will be consumed by the for loop
    
    # Row objects act like Python named tuples
    for row in result:
        print(f"x: {row.x}  y: {row.y}")

    # Result.mappings() returns a list of RowMapping objects instead
    for dict_row in result.mappings():
        x = dict_row["x"]
        y = dict_row["y"]
        print(x)
        print(y)

# send parameters safely with colon format, a.k.a. "bound parameters"
# always use bound parameters
with engine.connect() as conn:
    result = conn.execute(text("SELECT x, y FROM some_table WHERE y > :y"), {"y": 2})
    for row in result:
        print(f"x: {row.x}  y: {row.y}")

# if multiple parameters are provided, it will execute once for each item (with some optimization)
with engine.connect() as conn:
    conn.execute(
        text("INSERT INTO some_table (x, y) VALUES (:x, :y)"),
        [{"x": 11, "y": 12}, {"x": 13, "y": 14}],
    )
    conn.commit()

# ORM
# using Session instead, it's basically the same syntax as engine.connect()
stmt = text("SELECT x, y FROM some_table WHERE y > :y ORDER BY x, y")
with Session(engine) as session:
    result = session.execute(stmt, {"y": 6})
    for row in result:
        print(f"x: {row.x}  y: {row.y}")

# same paradigm applies: "commit as you go" or "begin once"
# "commit as you go"
with Session(engine) as session:
    result = session.execute(
        text("UPDATE some_table SET y=:y WHERE x=:x"),
        [{"x": 9, "y": 11}, {"x": 13, "y": 15}],
    )
    session.commit()

# "begin once"
with Session(engine) as session:
    with session.begin():
        # db operations
        pass

# "begin once" can also be written more succinctly:
with Session(engine) as session, session.begin():
    # db operations
    pass
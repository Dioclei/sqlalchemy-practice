from sqlalchemy import insert
from sqlalchemy.orm import Session

from ch1_engine import engine
from ch3_metadata import user_table, address_table, User, Address

########################
######## INSERT ########
######################## 

# using Insert construct to define INSERT SQL statements
stmt = insert(user_table).values(name="spongebob", fullname="Spongebob Squarepants")
# we can stringify these expressions to see the underlying SQL
print(stmt)
# we can get the Compiled object using ClauseElement.compile() method
compiled = stmt.compile()
# Compiled object also exposes the bound parameters via params
print(compiled.params)

# executing the statement is the same as previously with text() and passing bound parameters
with engine.connect() as conn:
    result = conn.execute(stmt)
    conn.commit()
# usually the INSERT statement does not return any rows. 
# if only 1 row is inserted it can contain information about it.
print(result.inserted_primary_key)

# the Insert construct generates VALUES automatically, even without defining it
print(insert(user_table))
# we can use this fact to execute it and pass in the bound parameters ourselves
# - in the below code block, we use this to insert with a list of parameters at once (executemany)
# - like in ch2, this will insert one row at a time
# - unlike ch2, we didn't need to spell out any SQL
with engine.connect() as conn:
    result = conn.execute(
        insert(user_table),
        [
            {"name": "sandy", "fullname": "Sandy Cheeks"},
            {"name": "patrick", "fullname": "Patrick Star"},
        ],
    )
    conn.commit()

# here we populate the address table as well so we have more interesting data for later portions
# don't worry too much about the code here, usually people will use ORM syntax to do this
from sqlalchemy import select, bindparam
scalar_subq = (
    select(user_table.c.id)
    .where(user_table.c.name == bindparam("username"))
    .scalar_subquery()
)

with engine.connect() as conn:
    result = conn.execute(
        insert(address_table).values(user_id=scalar_subq),
        [
            {
                "username": "spongebob",
                "email_address": "spongebob@sqlalchemy.org",
            },
            {"username": "sandy", "email_address": "sandy@sqlalchemy.org"},
            {"username": "sandy", "email_address": "sandy@squirrelpower.org"},
        ],
    )
    conn.commit()

# INSERT...RETURNING to return the affected rows
insert_stmt = insert(address_table).returning(
    address_table.c.id, address_table.c.email_address
)
print(insert_stmt)

# INSERT...FROM SELECT to compose an INSERT that gets rows directly from a SELECT
select_stmt = select(user_table.c.id, user_table.c.name + "@aol.com")
insert_stmt = insert(address_table).from_select(
    ["user_id", "email_address"], select_stmt
)
print(insert_stmt)

# INSERT...FROM SELECT...RETURNING
# we can combine the two statements above too
select_stmt = select(user_table.c.id, user_table.c.name + "@aol.com")
insert_stmt = insert(address_table).from_select(
    ["user_id", "email_address"], select_stmt
)
print(insert_stmt.returning(address_table.c.id, address_table.c.email_address))

# note that RETURNING is also supported for UPDATE and DELETE statements.


########################
######## SELECT ########
######################## 

from sqlalchemy import select

# similar to insert, select can also be stringified to show the underlying SQL
stmt = select(user_table).where(user_table.c.name == "spongebob")
print(stmt)

# similarly, to actually run the statement we need to execute it
with engine.connect() as conn:
    for row in conn.execute(stmt):
        print(row)

# ORM syntax, it's very similar but using ORM mapped classes instead
stmt = select(User).where(User.name == "spongebob")
with Session(engine) as session:
    for row in session.execute(stmt):
        print(row)

# FROM
# - note that FROM clause is inferred by the tables needed for the query (found in SELECT, WHERE, etc.)

# FROM - Core syntax
print(select(user_table))
# - specific columns
print(select(user_table.c.name, user_table.c.fullname))

# FROM - ORM syntax
# - note that when we do select(User) instead of each Row containing a tuple of column values,
# - we get instead Rows containing single-element-tuples of an instance of the class
print(select(User))
with Session(engine) as session:
    row = session.execute(select(User)).first()
    print(row)
    print(row[0])
# - to get a list of the instances instead of needing to do row[0] for each of them we can use session.scalars which selects the first "column" of the results
with Session(engine) as session:
    user = session.scalars(select(User)).first()
    print(user)
# - specific columns
print(select(User.name, User.fullname))
with Session(engine) as session:
    row = session.execute(select(User.name, User.fullname)).first()
    print(row)

    # we can also select from multiple tables, note that in this case columns for Address are inferred
    rows = session.execute(
        select(User.name, Address).where(User.id == Address.user_id).order_by(Address.id)
    ).all()
    print(rows)

# AS
# like AS in SQL, we can label SQL expressions with ColumnElement.label(), this works for both Core and ORM
# in this case we alias each row's "Username: " + user_table.c.name string as username, and access it later with row.username
stmt = select(
    ("Username: " + user_table.c.name).label("username"),
).order_by(user_table.c.name)
print(stmt)
with engine.connect() as conn:
    for row in conn.execute(stmt):
        print(f"{row.username}")

# WHERE
# we can use SQLAlchemy to compose SQL expressions with standard Python operators
print(user_table.c.name == "squidward")
print(address_table.c.user_id > 10)
print(select(user_table).where(user_table.c.name == "squidward"))
# use multiple where() to join expressions with AND
print(
    select(address_table.c.email_address)
    .where(user_table.c.name == "squidward")
    .where(address_table.c.user_id == user_table.c.id)
)
# can also use multiple expressions inside where() to join them with AND
print(
    select(address_table.c.email_address).where(
        user_table.c.name == "squidward",
        address_table.c.user_id == user_table.c.id,
    )
)
# for mixing AND and OR with parenthesizing
# - also note that the rendered SQL parenthesizing may not be exactly the same as the Python code (but functionally the result is the same)
from sqlalchemy import and_, or_
print(
    select(Address.email_address).where(
        and_(
            or_(User.name == "squidward", User.name == "sandy"),
            Address.user_id == User.id,
        )
    )
)
# for simple "equality" comparisons we can also use filter_by() which is quite popular
print(select(User).filter_by(name="spongebob", fullname="Spongebob Squarepants"))

# FROM and JOINs (explicit)
from sqlalchemy import func, desc
print(select(user_table.c.name))                                # table in COLUMNS -> table in FROM
print(select(user_table.c.name, address_table.c.email_address)) # multiple tables -> comma-separated tables in FROM (no JOIN)
print(                                                          # Select.join_from(): indicates left and right side of JOIN
    select(user_table.c.name, address_table.c.email_address).join_from(
        user_table, address_table
    )
)
print(                                                          # Select.join(): indicate only right side of join (left is inferred)
    select(user_table.c.name, address_table.c.email_address).join(address_table)
)
# note that ON clause of the join in Select.join_from() and Select.join() is inferred.
# difference between with join and without join:
stmt1 = select(user_table.c.name, address_table.c.email_address)
stmt2 = select(user_table.c.name, address_table.c.email_address).join(address_table)
with Session(engine) as session:
    print("stmt1")
    for item in session.execute(stmt1):
        print(item)
    print("stmt2")
    for item in session.execute(stmt2):
        print(item)
# Select.select_from() to make it more clear which table to select from and which to join to
print(select(address_table.c.email_address).select_from(user_table).join(address_table))
# for stuff like count(*) Select.select_from() is required because the FROM clause cannot be inferred
print(select(func.count("*")).select_from(user_table))

# ON (explicit)
# - Select.join() and Select.join_from() accept additional arguments to specify ON clause
# - note that for ORM we can also use the relationship() construct to do this (explained in later chapters)
print(
    select(address_table.c.email_address)
    .select_from(user_table)
    .join(address_table, user_table.c.id == address_table.c.user_id)
)
# by default, it's just JOIN (which is an INNER JOIN)
# LEFT OUTER JOIN
print(select(user_table).join(address_table, isouter=True))
# FULL OUTER JOIN
print(select(user_table).join(address_table, full=True))


# ORDER BY, GROUP BY, HAVING
print(select(user_table).order_by(user_table.c.name)) # default order (ascending)
print(select(User).order_by(User.fullname.desc()))    # descending, .asc() for ascending
# select all users with at least 2 addresses with GROUP BY + HAVING + aggregate COUNT function that aggregates over each user
stmt = (
    select(User.name, func.count(Address.id).label("count"))
    .join(Address)
    .group_by(User.name)
    .having(func.count(Address.id) > 1)
)
with engine.connect() as conn:
    result = conn.execute(stmt)
    print(result.all())
# we can also use labels in the ORDER BY or GROUP BY clauses with their name as a string
stmt = (
    select(Address.user_id, func.count(Address.id).label("num_addresses"))
    .group_by("user_id")
    .order_by("user_id", desc("num_addresses"))
)
print(stmt)


# Using Aliases with .alias() to reference tables multiple times
user_alias_1 = user_table.alias()
user_alias_2 = user_table.alias()
print(
    select(user_alias_1.c.name, user_alias_2.c.name).join_from(
        user_alias_1, user_alias_2, user_alias_1.c.id > user_alias_2.c.id
    )
)
# ORM Syntax uses aliased() function
from sqlalchemy.orm import aliased
address_alias_1 = aliased(Address)
address_alias_2 = aliased(Address)
print(
    select(User)
    .join_from(User, address_alias_1)
    .where(address_alias_1.email_address == "patrick@aol.com")
    .join_from(User, address_alias_2)
    .where(address_alias_2.email_address == "patrick@gmail.com")
)


# Subqueries and CTEs (common table expressions)
# - uses the Subquery and CTE objects, which come from Select.subquery() and Select.cte()
subq = (
    select(func.count(address_table.c.id).label("count"), address_table.c.user_id)
    .group_by(address_table.c.user_id)
    .subquery()
)
print(subq)
print(select(subq.c.user_id, subq.c.count)) # Subquery includes a Subquery.c column namespace
# - join subquery to user_account table
stmt = select(user_table.c.name, user_table.c.fullname, subq.c.count).join_from(
    user_table, subq
)
print(stmt)
# - for CTEs, the syntax is virtually the same but the rendered SQL will be different
subq = (
    select(func.count(address_table.c.id).label("count"), address_table.c.user_id)
    .group_by(address_table.c.user_id)
    .cte()
)
stmt = select(user_table.c.name, user_table.c.fullname, subq.c.count).join_from(
    user_table, subq
)
print(stmt)

# ORM subqueries, CTEs, and aliased()
# - by default the subquery columns need to be accessed with something like subq.c.id
# - wrapping with aliased() allows us to:
#   1. load the Address table and return ORM entities
#   2. access attributes with address_subq.id instead of Core syntax
#   3. enable ORM join syntax with the subquery
subq = select(Address).where(~Address.email_address.like("%@aol.com")).subquery()
address_subq = aliased(Address, subq)
stmt = (
    select(User, address_subq)
    .join_from(User, address_subq)
    .order_by(User.id, address_subq.id)
)
with Session(engine) as session:
    for user, address in session.execute(stmt):
        print(f"{user} {address}")
# same thing but with CTE instead of Subquery
cte_obj = select(Address).where(~Address.email_address.like("%@aol.com")).cte()
address_cte = aliased(Address, cte_obj)
stmt = (
    select(User, address_cte)
    .join_from(User, address_cte)
    .order_by(User.id, address_cte.id)
)
with Session(engine) as session:
    for user, address in session.execute(stmt):
        print(f"{user} {address}")

# UNION, UNION ALL, and other set operations
# operations like union_all() produce a CompoundSelect object, which is like a Select but with less operations
from sqlalchemy import union_all
stmt1 = select(user_table).where(user_table.c.name == "sandy")
stmt2 = select(user_table).where(user_table.c.name == "spongebob")
u = union_all(stmt1, stmt2)
with engine.connect() as conn:
    result = conn.execute(u)
    print(result.all())
# we can also create Subqueries from the union result (CompoundSelect)
u_subq = u.subquery()
stmt = (
    select(u_subq.c.name, address_table.c.email_address)
    .join_from(address_table, u_subq)
    .order_by(u_subq.c.name, address_table.c.email_address)
)
with engine.connect() as conn:
    result = conn.execute(stmt)
    print(result.all())
# ORM syntax with unions - how to get entities from unioned objects?
stmt1 = select(User).where(User.name == "sandy")
stmt2 = select(User).where(User.name == "spongebob")
u = union_all(stmt1, stmt2)
# - we can use from_statement() to link the union object to the mapped class
orm_stmt = select(User).from_statement(u)
with Session(engine) as session:
    for obj in session.execute(orm_stmt).scalars():
        print(obj)
# - or convert it to a subquery and use aliased() to link it to the mapped class
user_alias = aliased(User, u.subquery())
orm_stmt = select(user_alias).order_by(user_alias.id)
with Session(engine) as session:
    for obj in session.execute(orm_stmt).scalars():
        print(obj)


# SELECT section: 
# I will skip the following because I don't find them that relevant, since my focus now is to get the basics down.
# I also believe I can easily refer back to the documentation when I need them.
# - Scalar and Correlated Subqueries
# - LATERAL correlation
# - EXISTS
# - more details on Functions
# - window functions
# - type casting and coercion


#################################
######## UPDATE / DELETE ########
#################################

# Similar to insert(), update() will usually update against a single table at a time and does not return any rows.
# Note that some backends can update multiple tables at a time.
from sqlalchemy import update, bindparam
stmt = (
    update(user_table)
    .where(user_table.c.name == "patrick")
    .values(fullname="Patrick the Star")
)
print(stmt)
# Update.values() is basically the same as Insert.values(), specify parameters with column names as keyword arguments
stmt = update(user_table).values(fullname="Username: " + user_table.c.name)
print(stmt)
# possible to use bindparam for executemany context
stmt = (
    update(user_table)
    .where(user_table.c.name == bindparam("oldname"))
    .values(name=bindparam("newname"))
)
with engine.begin() as conn:
    conn.execute(
        stmt,
        [
            {"oldname": "jack", "newname": "ed"},
            {"oldname": "wendy", "newname": "mary"},
            {"oldname": "jim", "newname": "jake"},
        ],
    )

# deletes are pretty simple
from sqlalchemy import delete
stmt = delete(user_table).where(user_table.c.name == "patrick")
print(stmt)

# possible to get rowcount of UPDATE and DELETE
# - this value = number of rows matched by WHERE clause, it doesn't matter whether they were actually modified or not
# - not necessarily available, depends on DBAPI module, and if it's not available it will be -1
with engine.begin() as conn:
    result = conn.execute(
        update(user_table)
        .values(fullname="Patrick McStar")
        .where(user_table.c.name == "patrick")
    )
    print(result.rowcount)

# RETURNING with UPDATE, DELETE
update_stmt = (
    update(user_table)
    .where(user_table.c.name == "patrick")
    .values(fullname="Patrick the Star")
    .returning(user_table.c.id, user_table.c.name)
)
print(update_stmt)
delete_stmt = (
    delete(user_table)
    .where(user_table.c.name == "patrick")
    .returning(user_table.c.id, user_table.c.name)
)
print(delete_stmt)
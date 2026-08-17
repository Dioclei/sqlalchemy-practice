# for Core section
from sqlalchemy import MetaData
from sqlalchemy import Table, Column, Integer, String
from sqlalchemy import ForeignKey

# for ORM section
from sqlalchemy.orm import DeclarativeBase
from typing import List
from typing import Optional
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from ch1_engine import engine

# when defining the schema (tables, columns, etc.) we need a MetaData object to hold all of it
metadata_obj = MetaData()

# defining Tables, with various constraints
user_table = Table(
    "user_account",
    metadata_obj,
    Column("id", Integer, primary_key=True),
    Column("name", String(30)),
    Column("fullname", String),
)
print(user_table.primary_key)

# defining Tables with foreign key and nullable
address_table = Table(
    "address",
    metadata_obj,
    Column("id", Integer, primary_key=True),
    Column("user_id", ForeignKey("user_account.id"), nullable=False),
    Column("email_address", String, nullable=False),
)

# use create_all() to emit CREATE TABLE statements to the database
metadata_obj.create_all(engine)

# ORM
# use a DeclarativeBase, which contains:
# - an associated MetaData
# - a registry, which is where all the mapped classes coordinate with each other
class Base(DeclarativeBase):
    pass
print(Base.metadata)
print(Base.registry)

# define Tables by inheriting from the DeclarativeBase
# these classes are established as "ORM mapped classes" at class creation time, each typically referring to a Table object
# - these tables are named by assigning a string to the __tablename__ attribute
# - they use type annotations instead to define types and constraints
class User(Base):
    __tablename__ = "user_account"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(30))
    fullname: Mapped[Optional[str]]
    addresses: Mapped[List["Address"]] = relationship(back_populates="user")
    def __repr__(self) -> str:
        return f"User(id={self.id!r}, name={self.name!r}, fullname={self.fullname!r})"

class Address(Base):
    __tablename__ = "address"

    id: Mapped[int] = mapped_column(primary_key=True)
    email_address: Mapped[str]
    user_id = mapped_column(ForeignKey("user_account.id"))
    user: Mapped[User] = relationship(back_populates="addresses")
    def __repr__(self) -> str:
        return f"Address(id={self.id!r}, email_address={self.email_address!r})"

# each class is automatically given an __init__() method if not declared
# - consists of all attribute names as optional keyword arguments
sandy = User(name="sandy", fullname="Sandy Cheeks")

# similar to core, use MetaData.create_all() to emit the DDL to the database to create the tables
# - in this case the code still runs but doesn't actually create the tables since they are already created.
Base.metadata.create_all(engine)
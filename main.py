from typing import List, Optional
from sqlalchemy import String, ForeignKey, insert
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass

# the DeclarativeBase has its own MetaData collection and a registry
# the MetaData holds all definitions and other information pertaining to the database
# the Registry holds the "mapper configuration" and is central to mapped class operations
print(Base.metadata)
print(Base.registry)

# Table definitions
# each class has a "__tablename__" attribute where a string is assigned, to denote that it is a Table
# mapped_columns are used to indicate Columns in a Table
# - for simple datatypes, use Python's data types like int and str
# - for constraints, use sqlalchemy provided types like String
# - for nullable/non-nullable, use Optional
# - alternatively to type annotations, we can use mapped_column with more explicit parameters like nullable=False
# each class has is automatically given an __init__() method with all attribute names as optional keyword arguments
# - e.g. tom = User(name="tom", fullname="tom holland")
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

    user: Mapped[User] = relationship(back_populates="address")

    def __repr__(self) -> str:
        return f"Address(id={self.id!r}, email_address={self.email_address!r})"
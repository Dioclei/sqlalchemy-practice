from ch1_engine import engine
from ch3_metadata import User, Address
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.orm import selectinload, joinedload, contains_eager

# note that in the User class definition, we have
# - addresses: Mapped[List["Address"]] = relationship(back_populates="user")
# and in Address class definition, we have
# - user: Mapped["User"] = relationship(back_populates="addresses")


#
# Persisting and Loading Relationships
#

# the code below demonstrates what relationship() does

# initialize a User
u1 = User(name="pkrabs", fullname="Pearl Krabs")
print(u1.addresses) # empty list

# add an Address to the User
a1 = Address(email_address="pearl.krabs@gmail.com")
u1.addresses.append(a1)
print(u1.addresses) # we see the address, obviously

# relationship.back_populates helps to synchronize the Address object's user attribute
# NOTE: it is important to pass the related attribute name into relationship.back_populates,
#       to indicate that the relationships are complementary to each other
print(a1.user) # Pearl Krabs

# same happens for the opposite direction
a2 = Address(email_address="pearl@aol.com", user=u1) # equivalent to a2.user = u1
print(u1.addresses)

# there is a cascading effect when we add any 1 of the objects to a session:
with Session(engine) as session:
    # session.add(u1)
    # session.add(a1)
    session.add(a2)
    print(u1 in session)
    print(a1 in session)
    print(a2 in session)

    # the objects are still pending (to be INSERTed), so the related keys are None
    print(u1.id)
    print(a1.user_id)

    session.commit()
    # we can see that the required SQL statements for the relationships are executed
    # all transaction steps invoke in the correct order
    # automated values like the primary key (id) are also added in correctly

    # as per Session.commit.expire_on_commit all associated objects that were commited are now expired
    # as a result any time we try to read the objects / their related attributes again, a new lazy load will be emitted!
    print(u1.id)        # needs to emit SELECT for the User
    print(u1.addresses) # needs to emit SELECT for the related Addresses

    # as per lazy loading if we modify the objects in the ORM again it will not incur any db operations (until we commit/flush)
    # there are some optimizations: because the related Addresses were queried previously we can also access them without incurring db operations
    print(a1) # no SELECT
    print(a2) # no SELECT

#
# Using Relationships to JOIN
#

# pass class-bound attribute corresponding to relationship() as a single argument to Select.join() to infer both right side of JOIN and ON
print(select(Address.email_address).select_from(User).join(User.addresses))
# if you don't use the class-bound attribute, the relationship() is not used, but rather the ForeignKeyConstraint is used instead to infer the JOIN / ON
print(select(Address.email_address).join_from(User, Address))


#
# Loader Strategies
#

# N Plus One problem: 
# when several objects in ORM memory each refer to a handful of unloaded attributes, accessing them can cause many additional queries
# they are also emitted implicitly, so sometimes you don't even know they are being emitted

# Firstly, to solve this problem, before making any changes to code: test the application, turn on SQL echoing, and watch the SQL that is emitted.

# Next, there are a few "loader strategies" to resolve the problem, as represented by Select.options()

# Selectin Load - ensures that some data (obtained with SELECT) is loaded upfront without any WHEREs or JOINs
stmt = select(User).options(selectinload(User.addresses)).order_by(User.id)
with Session(engine) as session:
    for row in session.execute(stmt):
        print(
            f"{row.User.name}  ({', '.join(a.email_address for a in row.User.addresses)})"
        )

# Joined Load - good for many-to-one relationships, basically adds additional columns in the joined table to the original result
# note that Joined Load also works for one-to-many relationships but it will multiply out the number of rows recursively. For this, evaluate its use vs Selectin Load
stmt = (
    select(Address)
    .options(joinedload(Address.user, innerjoin=True))
    .order_by(Address.id)
)
for row in session.execute(stmt):
    print(f"{row.Address.email_address} {row.Address.user.name}")

# Explicit Join + Eager Load with contains_eager() - contains_eager assumes that the table is already joined
stmt = (
    select(Address)
    .join(Address.user)
    .where(User.name == "pkrabs")
    .options(contains_eager(Address.user))
    .order_by(Address.id)
)
for row in session.execute(stmt):
    print(f"{row.Address.email_address} {row.Address.user.name}")

# Raiseload - It is also possible to raise an exception on lazy loading for a certain relationship
# - this is done by setting lazy="raise_on_sql" in the relationship
# e.g.:
# - (User class)    addresses: Mapped[List["Address"]] = relationship(back_populates="user", lazy="raise_on_sql")
# - (Address class) user: Mapped["User"] = relationship(back_populates="addresses", lazy="raise_on_sql")
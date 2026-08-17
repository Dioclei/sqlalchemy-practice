from sqlalchemy import select
from sqlalchemy.orm import Session

from ch1_engine import engine
from ch3_metadata import User, Address

# insert some data that should initially be there based on past exercises
with Session(engine) as session:
    session.add(User(name="spongebob", fullname="Spongebob Squarepants"))
    session.add(User(name="sandy", fullname="Sandy Cheeks"))
    session.add(User(name="patrick", fullname="Patrick Star"))
    session.commit()

#
# Inserting Rows using the ORM Unit of Work pattern
#

# while classes represent the Table definitions, instances of those classes represent Rows (which can be INSERTed)
squidward = User(name="squidward", fullname="Squidward Tentacles")
krabs = User(name="ehkrabs", fullname="Eugene H. Krabs")
print(squidward) # pkey id is None since it's using the automatically increasing id

# Unit of Work pattern:
# - add objects to a Session to accumulate changes
# - flush objects to database by emitting when they are needed
# - code below demonstrates the Unit of Work pattern
session = Session(engine)
session.add(squidward)
session.add(krabs)
print(session.new) # show pending objects
session.flush() # flush changes to database
# note that .flush() is usually not needed because there is autoflush
# whenever Session.commit() is called, it also flushes out changes

# after flushing, observe that the id is no longer None
print(squidward.id)
print(krabs.id)

# now if we try to get the object by primary key (id), it works
some_squidward = session.get(User, 4)
print(some_squidward)
print(some_squidward is squidward) # True
session.commit()


#
# Updating ORM Objects using the Unit of Work pattern
#

# an UPDATE is emitted as part of the unit-of-work pattern, on a per-primary-key basis based on modified rows
sandy = session.execute(select(User).filter_by(name="sandy")).scalar_one()
print(sandy) # sandy now refers to the database row with a pkey of 2 in the current transaction
sandy.fullname = "Sandy Squirrel"   # if we alter the attributes, the Session tracks the change
print(sandy in session.dirty)       # True

# now we trigger an autoflush which always happens before a SELECT
sandy_fullname = session.execute(select(User.fullname).where(User.id == 2)).scalar_one()
print(sandy_fullname)               # "Sandy Squirrel" (changed)
print(sandy in session.dirty)       # False


#
# Deleting ORM Objects using the Unit of Work pattern
#

# an individual ORM object can be marked for deletion by the Session using Session.delete()
patrick = session.get(User, 3)
session.delete(patrick)
print(patrick in session) # True, patrick will stay in Session until the flush happens

session.execute(select(User).where(User.name == "patrick")).first() # we can see the DELETE preceding the SELECT
print(patrick in session) # False



#
# Rolling back
#

# calling session.rollback() has the effect of calling ROLLBACK on the transaction,
# and *expire* all objects currently associated with the session
print(sandy.__dict__) # we can see fullname, name, etc.
session.rollback()
print(sandy.__dict__) # some special internal state object (represents no state)

# objects are lazy loaded, so the attributes are only populated when we need them
print(sandy.fullname) # shows SELECT statement + original fullname
print(sandy.__dict__)

print(patrick in session) # True
print(session.execute(select(User).where(User.name == "patrick")).scalar_one() is patrick) # True, database data is back


#
# Closing a session
#

# if we open a session without with, i.e with Session(engine) as session:, then we should always do session.close()
# session.close() basically:
# - releases all connections to db
# - cancels out / rollbacks any transactions
# - expunges all objects, i.e. all objects associated with the session are now *detached*.
#   even if they were expired, they are now non-functional.
#   we can re-associate the detached object in a new session but it's not recommended.

session.close()

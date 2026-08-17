from sqlalchemy import create_engine

# create a sqlite database in-memory
engine = create_engine("sqlite+pysqlite:///:memory:", echo=True)

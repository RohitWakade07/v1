import sys
import os
sys.path.append(os.path.abspath("."))
from sqlalchemy import create_engine
from app.models.models import SQLModel

def dump(sql, *multiparams, **params):
    print(sql.compile(dialect=engine.dialect))
    print(";")

engine = create_engine("postgresql+psycopg2:///", strategy="mock", executor=dump)
SQLModel.metadata.create_all(engine, checkfirst=False)

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base,sessionmaker 


connection = "sqlite:///./shortener.db"


engine =create_engine(connection)

seesion_local = sessionmaker(autocommit=False,bind=engine)
Base = declarative_base()

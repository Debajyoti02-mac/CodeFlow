from sqlalchemy import Integer , Column , create_engine ,String
from sqlalchemy.orm import DeclarativeBase , sessionmaker 

URL = "sqlite:///.SQL_DataBase.db"

# Create engine 
engine = create_engine(url=URL,connect_args={'check_same_thread':False})
#Session create 
session = sessionmaker(bind=engine,autoflush=False , autocommit=False)
#Base 
class Base(DeclarativeBase):
    pass

# Database create 
class SQL_base(Base):
    __tablename__="Database"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=True)
    question = Column(String)
    limit = Column(Integer)
    answer = Column(String)
Base.metadata.create_all(bind=engine)

# Create connections 
def create_db():
    db=session()
    try : 
        yield db
    finally:
        db.close()
    
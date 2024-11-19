from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

class DatabaseConnector:
    def __init__(self, db_url="sqlite:///C:/HAL/IH/IH22/Ganger/app/model/database_manager/Ganger.db", echo=False):
        self.__db_url = db_url
        self.__engine = create_engine(self.__db_url, echo=echo)
        self.__Session = sessionmaker(bind=self.__engine)

        print("Database Path:", db_url)

    @property
    def engine(self):
        return self.__engine
    
    @property
    def session(self):
        return self.__Session()

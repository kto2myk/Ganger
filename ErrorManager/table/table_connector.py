from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

class TableConnector:
    def __init__(self, db_url=None, echo=False):
        self.__db_url = db_url or "sqlite:///C:/HAL/IH/IH22/ErrorManager/table/error_logs.db"
        self.__engine = create_engine(self.__db_url, echo=echo)
        self.__session = sessionmaker(bind=self.__engine)

        print(f"Database Path: {self.__db_url}")

    @property
    def engine(self):
        return self.__engine

    @property
    def session(self):
        return self.__session()

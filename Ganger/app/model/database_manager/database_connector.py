from sqlalchemy import create_engine
from sqlalchemy.orm import Session

class DatabaseConnector:
    def __init__(self, db_url="sqlite:///C:/HAL/IH/IH22/Ganger/app/model/database_manager/Ganger.db", echo=False):
        self.__db_url = db_url
        self.__engine = create_engine(self.__db_url, echo=echo)

    @property
    def engine(self):
        """
        データベースエンジンのインスタンスを返す。
        """
        return self.__engine
    
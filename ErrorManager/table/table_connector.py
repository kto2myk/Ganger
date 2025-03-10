from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))  # `database_manager.py` があるディレクトリ
DB_PATH = os.path.join(BASE_DIR, "error_logs.db")  # ✅ `database/` フォルダ内を参照
class TableConnector:
    def __init__(self, db_url=None, echo=False):
        self.__db_url = f"sqlite:///{DB_PATH}"         
        self.__engine = create_engine(self.__db_url, echo=echo)
        self.__session = sessionmaker(bind=self.__engine)
        
    @property
    def engine(self):
        return self.__engine

    @property
    def session(self):
        return self.__session()

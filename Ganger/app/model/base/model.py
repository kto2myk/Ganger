from sqlalchemy.orm import DeclarativeBase 

# すべてのORMモデルが継承するためのベースクラス
class Base(DeclarativeBase):
    pass

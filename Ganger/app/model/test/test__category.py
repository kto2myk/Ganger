from Ganger.app.model.model_manager.model import CategoryMaster
from Ganger.app.model.database_manager.database_manager import DatabaseManager
data = [
    "tops",
    "pants",
    "items",
    "other"
]
try:
    db_manager = DatabaseManager()
    for ctgr in data:
        filter = {"category_name":ctgr}
        db_manager.insert(model=CategoryMaster,
                        data=filter)
        print(f"{ctgr} is inserted successfully")

except Exception as e:
    print(e)
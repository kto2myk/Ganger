from Ganger.app.model.model_manager.model import CategoryMaster
from Ganger.app.model.database_manager.database_manager import DatabaseManager
from Ganger.app.view.app import app
data = [
    "clothes",
    "cap",
    "shoes",
    "accessories",
]
with app.test_request_context():
    try:
        db_manager = DatabaseManager(app)
        for ctgr in data:
            filter = {"category_name":ctgr}
            db_manager.insert(model=CategoryMaster,
                            data=filter)
            print(f"{ctgr} is inserted successfully")

    except Exception as e:
        print(e)
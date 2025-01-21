from Ganger.app.model.shop.shop_manager import ShopManager
from Ganger.app.model.database_manager.database_manager import DatabaseManager
from Ganger.app.model.database_manager.db_creator import TableManager
from Ganger.app.model.model_manager.model import Shop
from Ganger.app.view.app import app
# tbmanager = TableManager()
# tbmanager.drop_table(table_name="post_categories")


with app.test_request_context():

    try:
        shop_manager = ShopManager()
#         result = shop_manager.create_product(
#             post_id = 8,
#             price=int("6010"),
#             name="tested product",
#             category_name="items"
#             )
#         app.logger.info("ok") 
#     except Exception as e:
#         app.logger.error(e)
    

        db_manager = DatabaseManager()
        Session = db_manager.make_session()
        db_manager.session_close(Session)
        result = shop_manager.delete_product(
            product_id=1,
        )
        app.logger.info("delete")
    except Exception as e:
        app.logger.error(e)
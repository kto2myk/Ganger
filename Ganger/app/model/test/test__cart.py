from Ganger.app.model.shop.shop_manager import ShopManager
from Ganger.app.view.app import app

with app.test_request_context():
    try:
        shop_manager = ShopManager()
    #     result = shop_manager.add_cart_item(
    #         user_id=1,
    #         product_id=1,
    #         quantity=1
    #     )
    #     if result:
    #         app.logger.info(result)
    #     else:
    #         print(result)
        result = shop_manager.delete_cart_items(
            user_id=1,
            product_ids=1,
        )
        if result:
            app.logger.info(result)
        else:
            app.logger.warning("something went wrong")
    except Exception as e:
        app.logger.error(e)
            
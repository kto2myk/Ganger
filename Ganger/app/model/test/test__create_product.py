from Ganger.app.model.shop.shop_manager import ShopManager
from Ganger.app.view.app import app

with app.app_context():
    try:
        shop_manager = ShopManager()
        result = shop_manager.create_product(
            post_id = 3,
            price=int("4000"),
            name="tested product",
            category_name="items"
            )
        app.logger.info("ok",result) 
    except Exception as e:
        app.logger.error(e)
    
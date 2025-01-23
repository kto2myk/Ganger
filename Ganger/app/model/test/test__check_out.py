from Ganger.app.view.app import app
from Ganger.app.model.shop.shop_manager import ShopManager

with app.test_request_context():
    try:
        shop_manager = ShopManager()
        result = shop_manager.check_out(selected_cart_item_ids=[1],
                                        user_id=3,
                                        payment_method="credit card")
        app.logger.info(result)
    except Exception as e:
        app.logger.error(e)
from Ganger.app.model.database_manager.database_manager import DatabaseManager
from Ganger.app.model.notification.notification_manager import NotificationManager
from Ganger.app.model.model_manager.model import CategoryMaster,ProductCategory,Shop,Post,Like
from Ganger.app.model.validator.validate import Validator
from sqlalchemy.exc import SQLAlchemyError
from flask import current_app as app, session



class ShopManager(DatabaseManager):
    def __init__(self):
        super().__init__()
        self.__notification_manager = NotificationManager()
    
    def create_product(self, post_id, price, name, category_name, Session=None):
        """
        Shopテーブルに新しい商品を追加し、カテゴリを設定する
        :param post_id: 関連する投稿のID
        :param price: 商品の価格
        :param name: 商品の名前
        :param category_name: カテゴリ名
        :return: 辞書形式の結果 {status: bool, message: str, product: dict or None}
        """
        try:
            Session = self.make_session(Session)
            # データの準備
            product_data = {
                "post_id": post_id,
                "price": price,
                "name": name
            }

            # Step 1: 商品をShopテーブルに挿入
            inserted_product = self.insert(model=Shop, data=product_data, unique_check={"post_id": post_id}, Session=Session)
            if not inserted_product:
                error_result =  {"status": False, "message": "商品作成に失敗しました（重複の可能性）。", "product": None}
                raise Exception

            # Step 2: カテゴリを取得
            category_id = self.get_category(category_name, Session=Session)
            if not category_id:
                error_result = {"status": False, "message": f"カテゴリ '{category_name}' が見つかりません。", "product": None}
                raise Exception

            # Step 3: ProductCategoryテーブルに挿入
            product_category_data = {
                "category_id": category_id,
                "product_id": inserted_product["product_id"]
            }

            inserted_product_category = self.insert(
                model=ProductCategory,
                data=product_category_data,
                unique_check={"product_id": inserted_product["product_id"]},
                Session=Session
            )
            if not inserted_product_category:
                error_result = {"status": False, "message": "ProductCategoryテーブルへの挿入に失敗しました。", "product": None}
                raise Exception

            # Step 4: 通知作成
            user_ids = [like.user_id for like in self.fetch(model=Like, filters={"post_id": post_id}, Session=Session)]
            if user_ids:
                self.__notification_manager.create_full_notification(
                    sender_id=3,  # session ID の復号化などが必要
                    recipient_ids=user_ids,
                    type_name="Productized",
                    contents=f"あなたが「いいね」した投稿が商品化されました: {name}",
                    related_item_id=inserted_product["product_id"],
                    related_item_type="shop",
                    Session=Session
                )

            self.make_commit_or_flush(Session)
            return {
                "status": True,
                "message": f"商品化が成功しました: {inserted_product['name']}",
                "product": inserted_product
            }

        except Exception as e:
            self.session_rollback(Session)
            app.logger.error(e)
            return error_result
        
    def delete_product(self, product_id, Session=None):
        try:
            Session = self.make_session(Session)

            # 商品を削除
            is_deleted = self.delete(model=Shop, filters={"product_id": product_id}, Session=Session)

            if is_deleted:
                # 関連通知を削除
                deleted_notifications = self.__notification_manager.delete_notification(
                    related_item_id=product_id,
                    related_item_type="shop",
                    type_name="Productized",
                    Session=Session
                )
                result = {
                    "status": "deleted",
                    "product_id": product_id,
                    "deleted_notifications": deleted_notifications
                }
                app.logger.info(f"Product {product_id} deleted with {deleted_notifications} notifications.")
            else:
                result = {"status": "not_found", "product_id": product_id}
                app.logger.info(f"No product found with ID {product_id} to delete.")

            self.make_commit_or_flush(Session)
            return result
        except SQLAlchemyError as e:
            self.session_rollback(Session)
            app.logger.error(f"Failed to delete product {product_id}: {e}")
            raise

    def get_category(self, category_name,Session=None):
        """
        CategoryMasterテーブルからカテゴリを取得
        :param category_name: カテゴリ名
        :return: カテゴリID or None
        """
        try:
            Session = self.make_session(Session)
            # 既存のカテゴリを検索
            category = self.fetch_one(model=CategoryMaster, filters={"category_name": category_name},Session=Session)
            if  not category:
                # カテゴリが存在しない場合
                raise ValueError(f"カテゴリ '{category_name}' が見つかりません。")
            
            app.logger.info(f"カテゴリが見つかりました: {category.category_name}")
            self.pop_and_close(Session)
            return category.category_id

        except Exception as e:
            self.session_rollback(Session)
            app.logger.error(f"カテゴリ検索中にエラーが発生しました: {e}")
            return None
        except ValueError as e:
            self.session_rollback(Session)
            app.logger.warning(e)
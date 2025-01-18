from Ganger.app.model.database_manager.database_manager import DatabaseManager
from Ganger.app.model.notification.notification_manager import NotificationManager
from Ganger.app.model.model_manager.model import CategoryMaster,ProductCategory,Shop,Post
from sqlalchemy.exc import SQLAlchemyError
from flask import current_app as app



class ShopManager(DatabaseManager):
    def __init__(self):
        super().__init__()
        self.__notification_manager = NotificationManager()
    
    def create_product(self, post_id, price, name, category_name,Session=None):
        """
        Shopテーブルに新しい商品を追加し、カテゴリを設定する
        :param post_id: 関連する投稿のID
        :param price: 商品の価格
        :param name: 商品の名前
        :param category_name: カテゴリ名
        :return: 挿入された商品の辞書形式データ or None
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
            inserted_product = self.insert(model=Shop, data=product_data,unique_check={"post_id": post_id},Session=Session)
            if not inserted_product:
                raise SQLAlchemyError("商品作成に失敗しました。重複の可能性があります。")

            # Step 2: カテゴリを取得
            category_id = self.get_category(category_name,Session=Session)
            if not category_id:
                raise SQLAlchemyError(f"カテゴリ '{category_name}' が見つからないため、商品作成を中止しました。")

            # Step 3: ProductCategoryテーブルに挿入
            product_category_data = {
                "category_id": category_id,
                "product_id": inserted_product["product_id"]
            }

            inserted_product_category = self.insert(
                model=ProductCategory, 
                data=product_category_data,
                unique_check={"product_id": inserted_product["product_id"]},
                Session=Session)
            
            if not inserted_product_category:
                raise SQLAlchemyError("ProductCategoryテーブルへの挿入に失敗しました。")

            app.logger.info(f"新しい商品とカテゴリが作成されました: {inserted_product}, Category: {category_name}")

            self.make_commit_or_flush(Session)
            return inserted_product

        except (Exception ,SQLAlchemyError)as e:
            self.session_rollback(Session)
            app.logger.error(e)
            return None
        

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
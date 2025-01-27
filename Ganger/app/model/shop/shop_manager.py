from Ganger.app.model.database_manager.database_manager import DatabaseManager
from Ganger.app.model.notification.notification_manager import NotificationManager
from Ganger.app.model.model_manager.model import CategoryMaster,ProductCategory,Shop,Post,Like,Cart,CartItem,Sale,SalesItem
from Ganger.app.model.validator.validate import Validator
from sqlalchemy import desc
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import SQLAlchemyError
from decimal import Decimal
from flask import current_app as app, session,url_for



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


    def get_shop_with_images(self, limit=10,Session=None):
        """Shopの情報と関連する投稿画像を投稿時間の降順で取得し、Jinja2で使用できる形で返す"""
        try:
            Session = self.make_session(Session)
            results = (
                Session.query(Shop)
                .join(Post, Shop.post_id == Post.post_id)  # Postとの内部結合
                .options(joinedload(Shop.post).joinedload(Post.images))  # リレーションをロード
                .order_by(desc(Post.post_time))  # 投稿時間の降順（最新順）
                .limit(limit)  # 取得数制限
                .all()
            )

            if not results:
                self.session_rollback(Session)
                app.logger.warning("ショップデータが見つかりませんでした")
                return None

            formatted_data = []
            for shop in results:
                try:
                    shop_data = {
                        "product_id":Validator.encrypt(shop.product_id),
                        "img_path":url_for("static", filename=f"images/post_images/{shop.post.images[0].img_path}")
                    }
                    formatted_data.append(shop_data)
                except AttributeError as e:
                    app.logger.error(f"データ整形エラー: {e}")
                    continue
            self.pop_and_close(Session)
            return formatted_data

        except Exception as e:
            app.logger.error(f"エラーが発生しました: {e}")
            self.session_rollback(Session)
            return None
        
    def fetch_one_product_images(self,product_id,Session=None):
        try:
            product_id = Validator.decrypt(product_id)
            Session = self.make_session(Session)
            product = Session.query(Shop).options(joinedload(Shop.post).joinedload(Post.images)).filter(Shop.product_id==product_id).first()

            formatted_product = {
                "product_id":Validator.encrypt(product.product_id),
                "post_id":Validator.encrypt(product.post.post_id),
                "name":product.name,
                "price":float(product.price),
                "created_at":Validator.calculate_time_difference(product.created_at),
                "images": [
                        {"img_path": url_for("static", filename=f"images/post_images/{image.img_path}")}
                        for image in product.post.images
                        ] if product.post.images else []
                    } if product else None
            self.pop_and_close(Session)
            return formatted_product
        
        except Exception as e:
            self.session_rollback(Session)
            app.logger.error(f"error発生:{e}")
            return None
        
    def add_cart_item(self, user_id, product_id, quantity,Session=None):
        try:
            user_id = Validator.decrypt(user_id)
            product_id = Validator.decrypt(product_id)
            Session = self.make_session(Session)

            # 1. ユーザーのカートを取得（なければ新規作成）
            cart = self.fetch_one(model=Cart, filters={"user_id":user_id},Session=Session)
            if not cart:
                cart = self.insert(model=Cart,data={"user_id":user_id},Session=Session)
                app.logger.info(f"new cart created,user_id: {user_id}")
                cart = self.fetch_one(model=Cart, filters={"user_id":user_id},Session=Session)
                
            # 2. カート内の商品がすでに存在するか確認
            cart_item = self.fetch_one(model=CartItem,filters={"cart_id":cart.cart_id,"product_id":product_id},Session=Session)

            # 商品が既にカートにある場合、数量を増やす
            if cart_item:
                cart_item.quantity += quantity
            else:
                #商品がカートにない場合、新規追加
                self.insert(model=CartItem,data={"cart_id":cart.cart_id,"product_id":product_id,"quantity":quantity},Session=Session)
            # 3. 変更を保存
            self.make_commit_or_flush(Session)
            return {"status": "success", "message": "カートに商品を追加しました"}
        
        except SQLAlchemyError as e:
            Session.rollback(Session)  # エラー時にロールバック
            app.logger.error(f"カートへの商品追加中にエラーが発生しました: {e}")
            return None
        except Exception as e:
            Session.rollback(Session)
            app.logger.error(f"予期しないエラー: {e}")
        
    def delete_cart_items(self, user_id, product_ids,Session=None):
        """
        指定されたカートアイテムを削除し、すべて削除された場合にカートも削除する。

        :param user_id: ユーザーID
        :param cart_item_ids: 削除対象のカートアイテムIDのリスト
        :return: 処理結果（成功/エラー）
        """
        try:
            # user_id = Validator.decrypt(user_id)
            
            Session = self.make_session(Session)
            # ユーザーのカートを取得
            cart = Session.query(Cart).filter_by(user_id=user_id).first()
            if not cart:
                app.logger.warning("カートが見つかりませんでした")
                self.session_rollback(Session) #rollback
                return None

            # 単一値の場合、リストに変換
            if isinstance(product_ids, int):
                product_ids = [product_ids]
            # product_ids = map(Validator.decrypt, product_ids)  # 復号化


            # 指定されたカートアイテムを削除
            deleted_count = (
                Session.query(CartItem)
                .filter(CartItem.cart_id == cart.cart_id, CartItem.product_id.in_(product_ids))
                .delete(synchronize_session=False)
            )
            Session.flush()
            # 残りのカートアイテム数を確認
            remaining_items = Session.query(CartItem).filter_by(cart_id=cart.cart_id).count()

            if remaining_items == 0:
                # すべての商品が削除された場合、カート自体を削除
                self.delete(model=Cart,filters={"user_id": user_id},Session=Session)
                self.make_commit_or_flush(Session)
                return {"status": "success", "message": "カートが削除されました"}
            self.make_commit_or_flush(Session)
            return {"status": "success", "message": f"{deleted_count} アイテムが削除されました"}

        except SQLAlchemyError as e:
            app.logger.error(f"カートアイテム削除中にエラーが発生しました: {e}")
            Session.rollback()
            return None   
        
    def fetch_cart_items(self, user_id, Session=None):
        """
        指定されたユーザーIDに紐づくカートアイテムを取得し、辞書形式で返却する

        :param user_id: ユーザーのID
        :param Session: SQLAlchemyセッション（オプション）
        :return: (成功フラグ, カートアイテムのリスト（辞書型）) or (False, None)
        """
        try:
            Session = self.make_session(Session)
            user_id = Validator.decrypt(user_id)

            # ユーザーのカートを取得し、一括ロードを適用
            cart = (
                Session.query(Cart)
                .filter(Cart.user_id == user_id)
                .options(
                    joinedload(Cart.cart_items)
                    .joinedload(CartItem.shop)
                    .joinedload(Shop.post)
                    .joinedload(Post.images)
                )
                .first()
            )

            if not cart:
                self.session_rollback(Session)
                return True, []  # カートが存在しない場合

            if not cart.cart_items:
                self.session_rollback(Session)
                return True, []  # カートはあるが商品が入っていない

            # カートデータの整形
            cart_data = [
                {
                    "cart_id": Validator.encrypt(item.cart_id),
                    "item_id": Validator.encrypt(item.item_id), # カートアイテムID
                    "product_id": Validator.encrypt(item.product_id),
                    "post_id": Validator.encrypt(item.shop.post.post_id) if item.shop.post else None,
                    "product_name": item.shop.name,
                    "price": float(item.shop.price),
                    "quantity": item.quantity,
                    "image_path": url_for("static", filename=f"images/post_images/{item.shop.post.images[0].img_path}")
                                if item.shop.post and item.shop.post.images else None,
                    "added_at": item.added_at.strftime("%Y-%m-%d %H:%M:%S")
                }
                for item in cart.cart_items
            ]

            self.pop_and_close(Session)
            return True, cart_data

        except SQLAlchemyError as e:
            self.session_rollback(Session)
            app.logger.error(f"カートアイテム取得エラー: {e}")
            return False, None

    def update_cart_quantity(self, user_id, product_id, new_quantity):
        """
        カート内の商品数量を更新

        :param user_id: ユーザーID
        :param product_id: 商品ID
        :param new_quantity: 新しい数量
        :return: 更新結果（成功/失敗）
        """
        try:
            Session = self.make_session()
            cart_item = Session.query(CartItem).filter_by(user_id=user_id, product_id=product_id).first()

            if cart_item:
                cart_item.quantity = new_quantity
                Session.commit()
                return {"success": True, "message": "カートの数量が更新されました"}
            else:
                return {"success": False, "message": "商品がカートに見つかりません"}
        except Exception as e:
            Session.rollback()
            return {"success": False, "message": f"エラー: {str(e)}"}


    def check_out(self, selected_cart_item_ids, user_id, payment_method,Session=None):
        """
        選択されたカートアイテムIDの商品のみ購入処理を行う

        Args:
            selected_cart_item_ids (list): 選択されたカートアイテムIDのリスト
            user_id (int): ユーザーID
            payment_method (str): 選択された決済方法（例: 'credit_card', 'paypal'）

        Returns:
            dict: 購入結果（成功/失敗）
        """
        try:
            Session = self.make_session()
            
            # 1. 選択されたカートアイテムの取得
            cart_items = Session.query(CartItem).options(
                joinedload(CartItem.shop)
            ).filter(CartItem.item_id.in_(selected_cart_item_ids)).all()

            if not cart_items:
                self.session_rollback(Session)
                message = "選択された商品が見つかりません。"
                app.logger.warning(message) # ログ出力
                return {"success": False, "message":message}

            # 2. クエリ結果が単一かリストかを動的に判定しつつ、トータルの合算を計算
            total_amount = (
                (single_item := cart_items[0]) and 
                (Validator.calc_subtotal(price= single_item.shop.price,quantity=single_item.quantity,discount=single_item.shop.discount))
                if len(cart_items) == 1 
                else sum(
                    (Validator.calc_subtotal(price=item.shop.price,quantity=item.quantity,discount=item.shop.discount))
                    for item in cart_items
                )
            )

            # 3. Sale レコードの作成（親テーブル）
            sale_data={
                "user_id":user_id,
                "total_amount":total_amount,
                "payment_method":payment_method,
                "payment_status":'unpaid',
                }

            sale = self.insert(model=Sale,data=sale_data,Session=Session)
            if not sale:
                self.session_rollback(Session)
                app.logger.error("Sale record creation failed")
                return {"success": False, "message": "購入処理中にエラーが発生しました。"}
            
            # 4. 子レコード（SalesItem）の作成（共通処理）
            try:
                sales_items_data = [
                {
                    "sale_id": sale['sale_id'],
                    "product_id": item.product_id,
                    "quantity": item.quantity,
                    "price": float(item.shop.price),
                    "subtotal": float(Validator.calc_subtotal(
                        price=item.shop.price, 
                        quantity=item.quantity, 
                        discount=item.shop.discount
                    ))
                }
                for item in cart_items
            ]
                
                Session.bulk_insert_mappings(SalesItem, sales_items_data)
                app.logger.info("sale_items completely created")

            except SQLAlchemyError as e:
                self.session_rollback(Session)
                app.logger.error(e)
                return {"success": False, "message": "購入処理中にエラーが発生しました。"}

            # 5. カートアイテムの削除
            delete_result = self.delete_cart_items(user_id=user_id, product_ids=[item.product_id for item in cart_items], Session=Session)

            if not delete_result or delete_result["status"] != "success":
                self.session_rollback(Session)
                app.logger.error("Failed to delete cart items")
                raise Exception("カートアイテムの削除に失敗しました")
            
            # 6. トランザクションの確定
            self.make_commit_or_flush(Session)
            app.logger.info("購入が完了しました")
            return {"success": True, "message": "購入が完了しました。", "sale_id": sale['sale_id']}
        
        except SQLAlchemyError as e:
            self.session_rollback(Session)
            return {"success": False, "message": f"購入処理中にエラーが発生しました: {str(e)}"}

        except Exception as e:
            self.session_rollback(Session)
            return {"success": False, "message": f"予期しないエラー: {str(e)}"}


    def fetch_sales_history(self, user_id, limit=10,Session=None):
        """
        ユーザーの購入履歴を取得する

        :param user_id: ユーザーID
        :param limit: 取得数の上限
        :param Session: SQLAlchemyセッション（オプション）
        :return: 購入履歴のリスト（辞書型） or None
        """
        try:
            Session = self.make_session(Session)
            user_id = Validator.decrypt(user_id)
            sales = (
                Session.query(Sale)
                .filter_by(user_id=user_id).options(joinedload(Sale.items).joinedload(SalesItem.shop).joinedload(Shop.post).joinedload(Post.images))
                .order_by(desc(Sale.date))
                .limit(limit)
                .all()
            )

            if not sales:
                self.session_rollback(Session)
                return {"status": False, "message": "購入履歴はありません。"}

            # 購入履歴を整形
            sales_data = [
                {
                    "sale_id": Validator.encrypt(sale.sale_id),
                    "total_amount": float(sale.total_amount),
                    "payment_method": sale.payment_method,
                    "payment_status": sale.payment_status,
                    "created_at": sale.date.strftime("%Y-%m-%d %H:%M:%S"),
                    "items": [
                        {
                            "item_id": Validator.encrypt(item.sale_item_id),
                            "product_id": Validator.encrypt(item.product_id),
                            "product_name": item.shop.name,
                            "quantity": item.quantity,
                            "price": float(item.price),
                            "subtotal": float(item.subtotal),
                            "image_url": url_for('static', filename=f"images/post_images/{item.shop.post.images[0].img_path}") 
                            if item.shop.post.images else None}
                        for item in sale.items
                    ]
                }
                for sale in sales
            ]
            self.pop_and_close(Session)
            return sales_data

        except SQLAlchemyError as e:
            self.session_rollback(Session)
            app.logger.error(f"購入履歴取得中にエラーが発生しました: {e}")
            return None
        

    def search_categories(self, query, Session=None):
        try:
            Session = self.make_session(Session)

            # 1. カテゴリー名を部分一致検索し、候補リストを取得
            categories = (
                Session.query(CategoryMaster)
                .filter(CategoryMaster.category_name.ilike(f"%{query}%"))
                .all()
            )

            if not categories:
                app.logger.info(f"No categories found for query: {query}")
                return []

            # カテゴリー名のみの結果リスト
            category_results = [{"category_name": category.category_name, "post_count": 0, "posts": []} for category in categories]

            category_ids = [category.category_id for category in categories]
            app.logger.info(f"Category IDs found: {category_ids}")

            # 2. カテゴリーに紐づく投稿を画像とともに一括取得
            results = (
                Session.query(
                    CategoryMaster.category_name,
                    Shop.product_id,
                    Post.post_id,
                    Post.body_text,
                    Post.post_time,
                    Image.img_path
                )
                .join(ProductCategory, CategoryMaster.category_id == ProductCategory.category_id)
                .join(Shop, Shop.product_id == ProductCategory.product_id)
                .join(Post, Post.post_id == Shop.post_id)
                .outerjoin(Image, Image.post_id == Post.post_id)  # 画像がない場合も考慮
                .filter(CategoryMaster.category_id.in_(category_ids))
                .order_by(Image.img_order)
                .all()
            )

            app.logger.info(f"Total posts retrieved: {len(results)}")

            # 投稿データの整形
            post_data = {}
            for category_name, product_id,post_id, body_text, post_time, img_path  in results:
                if post_id not in post_data:
                    post_data[post_id] = {
                        "post_id": Validator.encrypt(post_id),
                        "product_id": Validator.encrypt(product_id),
                        "body_text": body_text,
                        "post_time": Validator.calculate_time_difference(post_time),
                        "category_name": category_name,
                        "image_url": url_for('static', filename=f"images/post_images/{img_path}") if img_path else None
                    }                    

            # カテゴリー結果に紐づく投稿を挿入
            for category in category_results:
                category["posts"] = [post for post in post_data.values() if post["category_name"] == category["category_name"]]
                category["post_count"] = len(category["posts"])

            self.pop_and_close(Session)
            app.logger.info(f"Final formatted results: {len(category_results)} categories")

            return category_results

        except Exception as e:
            self.session_rollback(Session)
            app.logger.error(f"Error in search_categories: {e}")
            return []

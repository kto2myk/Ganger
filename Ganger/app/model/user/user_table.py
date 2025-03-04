import os
from werkzeug.security import generate_password_hash, check_password_hash # パスワードハッシュ化用
from werkzeug.utils import secure_filename
from Ganger.app.model.database_manager.database_manager import DatabaseManager # データベース操作用
from Ganger.app.model.notification.notification_manager import NotificationManager
from Ganger.app.model.post.post_manager import PostManager
from Ganger.app.model.model_manager.model import User,Post,Follow,Block,Repost,CartItem,Shop,Like,SavedPost,SavedProduct
from flask import session, url_for  # セッション管理、画像パス生成用
from Ganger.app.model.validator.validate import Validator # バリデーション用
from Ganger.app.model.model_manager.model import User # ユーザーテーブル
from sqlalchemy.orm import Session, joinedload# セッション管理、リレーション取得用
from sqlalchemy import or_,and_,func,case,exists # OR検索用
from sqlalchemy.exc import SQLAlchemyError # データベースエラー用
import uuid # ランダムID生成用


class UserManager(DatabaseManager):
    def __init__(self,app=None):
        super().__init__(app)
        self.notification_manager = NotificationManager()


    def create_user(self, username: str, email: str, password: str,Session=None):
        """
        ユーザー作成処理を行い、成功時にセッションを登録。
        """
        randomid = str(uuid.uuid4())[:8]
        user_id = f"{username}_{randomid}"
        # Session = self.make_session(Session)
        try:
            Session = self.make_session(Session)
            # Email形式の検証
            Validator.validate_email_format(email)

            # ユーザー作成
            user_data = {
                "user_id": user_id,
                "username": username,
                "email": email,
                "password": generate_password_hash(password)
            }
            new_user = self.insert(User, user_data, unique_check={"email": email},Session=Session)

            if not new_user:
                raise ValueError("このメールアドレスは既に使用されています。")

            # セッション登録
            self.register_session(new_user)
            self.redis.add_score(ranking_key=self.trending[4],item_id=new_user['id'],score=1)
            self.make_commit_or_flush(Session)
            return True, new_user

        except ValueError as ve:
            self.session_rollback(Session)
            self.app.logger.error(f"[ERROR] Validation error: {ve}")
            self.error_log_manager.add_error(None, str(ve))
            return False, str(ve)
        except Exception as e:
            self.session_rollback(Session)
            self.app.logger.error(f"[ERROR] Unexpected error: {e}")
            self.error_log_manager.add_error(None, str(e))
            return False, str(e)

    def login(self, identifier: str, password: str,Session=None):
        """
        メールアドレスまたはユーザーIDでログイン。成功時にセッションを登録。
        """
        try:
            Session = self.make_session(Session)
            # ユーザー検索
            user = self.fetch_one(User, filters={"email": identifier},Session=Session) or self.fetch_one(User, filters={"user_id": identifier},Session=Session)
            if not user or not check_password_hash(user.password, password):
                raise Exception("ユーザー名またはパスワードが間違っています。")
            # セッション登録
            self.register_session(user)
            self.redis.add_score(ranking_key=self.trending[4],item_id=user.id,score=1)
            self.pop_and_close(Session)
            return user, None

        except Exception as e:
            self.session_rollback(Session)
            self.error_log_manager.add_error(None, str(e))
            return None, str(e)


    @staticmethod
    def register_session(data, keys=None, custom_logic=None):
        """
        セッションにデータを登録する
        :param data: 辞書型またはクラスのインスタンス
        :param keys: セッションに登録するキーのリスト（指定がない場合はすべて登録）
        :param custom_logic: 特殊処理用の辞書（key: 処理するキー, value: 関数）
        """
        # SQLAlchemyモデルの場合、辞書形式に変換
        if hasattr(data, "__dict__"):
            source = {key: value for key, value in vars(data).items() if not key.startswith("_")}
        elif isinstance(data, dict):
            source = data
        else:
            raise ValueError("渡されたデータは辞書型でもクラスのインスタンスでもありません。")

        # セッションに登録
        for key in (keys or source.keys()):
            if key in source:
                value = source[key]

                # 特殊処理: IDを暗号化
                if "id" in key.lower():  # "id" を含むキー名を検出
                    session[key] = Validator.encrypt(value)
                elif custom_logic and key in custom_logic:
                    session[key] = custom_logic[key](value)  # カスタムロジック適用
                else:
                    session[key] = value  # 通常の登録処理
        else:
            session.modified = True
                
        # プロフィール画像の特殊処理
        if "profile_image" in source and source["profile_image"]:
            session["profile_image"] = url_for("static", filename=f"images/profile_images/{source['profile_image']}")
            session.modified = True
        else:
            session["profile_image"] = url_for("static", filename="images/profile_images/default.png")

    def search_users(self, query,Session=None):
        """
        指定されたクエリに基づいてユーザーを検索し、結果を返す。
        """
        try:
            Session = self.make_session(Session)
            users = Session.query(User).filter(
                or_(
                    User.user_id.ilike(f"%{query}%"),
                    User.username.ilike(f"%{query}%")
                )
            ).limit(10).all()

            result = []  # 🔹 結果を格納するリストを作成
            for user in users:
                self.redis.add_score(ranking_key=self.trending[4],item_id=user.id,score=3)
                user_data = {
                    "user_id": user.user_id,
                    "username": user.username,
                    "id": Validator.encrypt(user.id),
                    "profile_image":url_for("static", filename=f"images/profile_images/{user.profile_image}")
                }
                result.append(user_data) 
            self.pop_and_close(Session)
            return result
        
        except SQLAlchemyError as e:
            self.session_rollback(Session)
            self.app.logger.error(f"Failed to search users: {e}")
            raise

    def get_followed_users(self, user_id, Session=None):
        """
        指定したユーザーがフォローしているユーザーを取得する。
        フォローしている人がいない場合、ランダムで10人のユーザーを取得する。
        """
        Session = self.make_session(Session)
        try:
            user_id = Validator.decrypt(user_id)
            # **フォローしている人がいるかを事前チェック**
            has_follows = Session.query(exists().where(Follow.user_id == user_id)).scalar()

            if has_follows:
                # **フォローしているユーザーを取得（リレーションを活用）**
                followed_users = (
                    Session.query(User.id, User.username, User.profile_image)
                    .join(Follow, Follow.follow_user_id == User.id)
                    .filter(Follow.user_id == user_id)
                    .order_by(func.random())
                    .limit(10)
                    .all()
                )

            else:
                # **フォローが0人の場合、ランダムに10人を取得**
                followed_users = (
                    Session.query(User.id, User.username, User.profile_image)
                    .order_by(func.random())  # SQLiteなら `random()`, PostgreSQLなら `RANDOM()`
                    .limit(10)
                    .all()
                )

            # **データを辞書リストに変換**
            users_data = [
                {"id": Validator.encrypt(user.id), "username": user.username, "profile_image": url_for("static", filename=f"images/profile_images/{user.profile_image}")}
                for user in followed_users
            ]

            self.pop_and_close(Session)
            return {"success": True, "result": users_data}

        except Exception as e:
            self.session_rollback(Session)
            return {"success": False, "result": str(e)}
            
    def updata_user_info(self,user_id=None,username=None,real_name=None,address=None,bio=None,profile_image=None,Session=None):
        """
        ユーザーの情報の更新を一括で請け負うメソッド。更新されるデータがある場合、自動でNONEが解除され更新される。
        """
        from Ganger.app.model.post.post_manager import PostManager
        post_manager = PostManager()
        try:
            Session = self.make_session(Session)
            user_info = [data.strip() if isinstance(data, str) else data for data in [user_id, username, real_name, address, bio] if data is not None]

            id = Validator.decrypt(session["id"])

            user = Session.query(User).filter_by(id=id).first()
            self.app.logger.info(user)

            if not user:
                self.session_rollback(Session)
                raise ValueError("存在しないユーザーです")
            
            if user_info[0]: #! 重複なしを確認
                Validate_user_id = Session.query(User).filter_by(user_id=user_id).first()
                if not Validate_user_id:
                    user.user_id = user_info[0]
                else:
                    raise ValueError(f"user_id{user_id}は既に存在しています。")
            if user_info[1]:
                user.username = user_info[1]
            if user_info[2]:
                user.real_name = user_info[2]
            if user_info[3]:
                user.address = user_info[3]
            if user_info[4]:
                user.bio = user_info[4]
            if profile_image: #! 画像保存処理を作成
                user_id = user_id if user_id else session['user_id']
                original_filename = secure_filename(profile_image.filename)

                if not post_manager.is_allowed_extension(original_filename):
                    raise ValueError(f"File type not allowed: {original_filename}")
                
                ext = os.path.splitext(original_filename)[1].lower()
                filename = f"{user_id}_{ext}"
                file_path = os.path.join(self.app.config['PROFILE_FOLDER'], filename)

                post_manager.save_file(file=profile_image, file_path=file_path)

                user.profile_image = filename

            Session.flush()
            user = Session.query(User).filter_by(id=id).first()
            self.register_session(user)
            self.make_commit_or_flush(Session)

            session.pop('id',None)
            return {"success":True, "message":"ユーザー情報が更新されました"}
        
        except ValueError as ve:
            self.session_rollback(Session)
            self.app.logger.error(ve)
            return {"success":False,"message":ve}
        
        except Exception as e:
            self.session_rollback(Session)
            self.app.logger.error(e)
            return    {"success":False, "message":"ユーザー情報更新に失敗しました"}

    def delete_user(self, Session=None):
        try:

            # セッション作成
            Session = self.make_session(Session)
            user_id = Validator.decrypt(session.get('id'))
            # ユーザーの投稿IDを取得
            post_ids = [post.post_id for post in Session.query(Post).filter_by(user_id=user_id).all()]
            self.app.logger.info(f"User {user_id} has {len(post_ids)} posts to delete.")

            # 投稿の削除（画像を削除するために `delete_post` を使用）
            if post_ids:
                post_manager = PostManager()
                delete_result = post_manager.delete_post(post_ids, Session=Session)
                if not delete_result["success"]:
                    self.pop_and_close(Session)
                    return delete_result  # 投稿削除でエラーが出た場合はそのまま返す

            # ユーザー削除（カスケード設定あり）
            user = Session.query(User).filter_by(id=user_id).first()
            if not user:
                raise Exception("User not found")
            else:
                if user.profile_image != "default-profile.png":
                    profile_folder = self.app.config['PROFILE_FOLDER']
                    img_path = os.path.join(profile_folder, user.profile_image)
                    if os.path.exists(img_path):
                        os.remove(img_path)
                        self.app.logger.info("delete profile_image")
                    else:
                        self.app.logger.warning("profile path not found")

            Session.delete(user)
            self.make_commit_or_flush(Session)
            self.app.logger.info(f"User {user_id} deleted successfully.")

            return {"success": True, "message": f"User {user_id} deleted successfully"}

        except Exception as e:
            self.app.logger.error(f"Error occurred in delete_user: {str(e)}", exc_info=True)
            self.session_rollback(Session)
            return {"success": False, "message": f"Failed to delete user: {str(e)}"}

            
    def get_user_profile_with_posts(self, user_id,Session=None):
        """
        指定されたユーザーIDのプロフィール情報と投稿データを取得。

        Args:
            user_id (str): 暗号化されたユーザーID。

        Returns:
            dict: プロフィール情報と投稿データのリスト。
        """
        try:
            # 暗号化されたユーザーIDを復号化
            decrypted_id = Validator.decrypt(user_id)
            user_id   = Validator.decrypt(session.get('id'))

            Session = self.make_session(Session)
            # ユーザー情報を取得
            user = Session.query(User).filter_by(id=decrypted_id).one_or_none()
            if not user:
                raise ValueError("ユーザーが見つかりません。")

            is_block= Session.query(Session.query(Block)
                .filter_by(user_id=user_id, blocked_user=decrypted_id)
                .exists()).scalar()
            is_blocked = Session.query(Session.query(Block)
                .filter_by(user_id=decrypted_id, blocked_user=user_id)
                .exists()).scalar()
            # ブロックしている場合はブロック情報のみ返す
            if is_block or is_blocked:
                profile_data = {
                    "is_block":is_block,
                    "is_blocked":is_blocked,
                    "id": Validator.encrypt(user.id),
                    "user_id": user.user_id,
                    "username": user.username,
                    "profile_image": url_for("static", filename=f"images/profile_images/{user.profile_image}"),
                }
                self.pop_and_close(Session)
                return profile_data
            
            result_follow = Session.query(
                Session.query(Follow).filter(Follow.follow_user_id == decrypted_id).count(),  # フォロワー数
                Session.query(Follow).filter(Follow.user_id == decrypted_id).count(),  # フォロー数
                Session.query(Follow)
                    .filter(Follow.user_id == user_id, Follow.follow_user_id == decrypted_id)
                    .exists()
            ).first()

            # データがない場合のデフォルト値を設定
            if result_follow is None:
                result_follow = (0, 0, False)

            # タプルのアンパック
            follower_count, following_count, is_follow = result_follow 

            posts = (
                Session.query(Post)
                .filter(Post.user_id == decrypted_id, Post.reply_id == None) # NULL判定を追加
                .options(joinedload(Post.images))  # 画像を一度に取得
                .order_by(Post.post_time.desc())  # 投稿時間で降順ソート
                .all()
            )
            # 投稿情報を整形
            formatted_posts = [
                {
                    "post_id": Validator.encrypt(post.post_id),
                    "first_image": (
                        url_for("static", filename=f"images/post_images/{post.images[0].img_path}")
                        if post.images else None  # 最初の画像のみ取得
                    ),
                }
                for post in posts
            ]

            # プロフィール情報を整形
            profile_data = {
                "is_me":decrypted_id == user_id,
                "is_block":False,
                "follower_count":follower_count,
                "following_count":following_count,
                "is_follow":is_follow > 0,
                "id": Validator.encrypt(user.id),
                "user_id": user.user_id,
                "username": user.username,
                "bio":user.bio,
                "profile_image": url_for("static", filename=f"images/profile_images/{user.profile_image}"),
                "posts": formatted_posts,
            }
            self.redis.add_score(ranking_key=self.trending[4],item_id=decrypted_id,score=8)
            self.pop_and_close(Session)
            return profile_data
        
        except SQLAlchemyError as db_error:
            self.session_rollback(Session)
            self.app.logger.error(f"Database error: {db_error}")
            raise
        except Exception as e:
            self.session_rollback(Session)
            self.app.logger.error(f"Unexpected error: {e}")
            raise

    def toggle_follow(self, followed_user_id,Session=None):
        """
        フォロー機能を切り替えるメソッド

        :param follow_user_id: フォロー対象のユーザーID
        :param sender_id: フォローを行うユーザーID
        :return: 処理結果を表す辞書
        """
        try:
            followed_user_id = Validator.decrypt(followed_user_id)
            sender_id = Validator.decrypt(session.get('id'))
            Session = self.make_session(Session) #Session maker
            data = {'follow_user_id':followed_user_id , 'user_id': sender_id}
            existing_follow = self.fetch_one(model=Follow, filters=data, Session=Session)

            if existing_follow:
                # フォローが存在する場合は削除
                self.delete(model=Follow, filters=data, Session=Session)
                self.notification_manager.delete_notification(
                    related_item_id=sender_id,
                    related_item_type="user",
                    type_name="follow",
                    sender_id=sender_id,
                    recipient_id=followed_user_id,
                    Session=Session
                )
                self.app.logger.info(f"Follow removed: followed_user={sender_id}, user_id={sender_id}")
                self.redis.add_score(ranking_key=self.trending[4],item_id=followed_user_id,score=-15)
                result = {"status": "unfollowed"}
            else:
                # フォローが存在しない場合は作成
                self.insert(model=Follow, data=data, Session=Session)
                self.app.logger.info(f"Follow added: followed_user={followed_user_id}, user_id={sender_id}")
                self.notification_manager.create_full_notification(
                    sender_id=sender_id,
                    recipient_ids=followed_user_id,
                    type_name="follow",
                    contents=f"{session.get('username')}さんがあなたをフォローしました。",
                    related_item_id=sender_id,
                    related_item_type="user",
                    Session=Session
                )
                self.redis.add_score(ranking_key=self.trending[4],item_id=followed_user_id,score=15)
                result = {"status": "followed"}

            self.make_commit_or_flush(Session)
            return result

        except Exception as e:
            self.session_rollback(Session)
            self.app.logger.error(f"Failed to toggle follow: {e}")
            self.error_log_manager.add_error(sender_id, str(e))
            raise

    
    def toggle_block(self,blocked_user_id,Session=None):
        """ ユーザーのブロック・ブロック解除を切り替える """
        try:
            user_id = Validator.decrypt(session.get('id'))
            blocked_user_id = Validator.decrypt(blocked_user_id)
            Session=self.make_session(Session)
            # 既にブロックしているか確認
            existing_block = Session.query(Block).filter_by(user_id=user_id, blocked_user=blocked_user_id).first()
            
            if existing_block:
                # すでにブロックしている場合 → ブロック解除
                Session.delete(existing_block)
                self.make_commit_or_flush(Session)
                self.app.logger.info("ブロックを解除しました")
                return {"message": "ブロックを解除しました", "status": "unblocked"}
            else:

                # ブロックを追加
                data = {'user_id': user_id, 'blocked_user': blocked_user_id}
                new_block = self.insert(model=Block, data=data, Session=Session)
                self.delete_related_data(user_id=user_id, blocked_user_id=blocked_user_id, Session=Session)

                self.make_commit_or_flush(Session)
                self.redis.add_score(ranking_key=self.trending[4],item_id=user_id,score=-5)
                self.app.logger.info("ユーザーをブロックしました", new_block)
                return {"message": "ユーザーをブロックしました", "status": "blocked"}

        except SQLAlchemyError as e:
            self.session_rollback(Session)  # 例外発生時にロールバック
            return {"error": f"処理中にエラーが発生しました: {str(e)}"}        
        

    def delete_related_data(self,user_id, blocked_user_id,Session=None):
        """
        ブロック時に関連データをすべて削除する（手動で削除）
        """
        try:
            Session = self.make_session(Session)
            #  フォロー解除（相互フォローも含めて削除）
            Session.query(Follow).filter(
                or_(
                    and_(Follow.user_id == user_id, Follow.follow_user_id == blocked_user_id),
                    and_(Follow.user_id == blocked_user_id, Follow.follow_user_id == user_id)
                )
            ).delete(synchronize_session=False)

            #  Repost削除（親の投稿が相手のものか確認）
            Session.query(Repost).filter(
                Repost.user_id == user_id,
                Repost.post.has(Post.user_id == blocked_user_id)
            ).delete(synchronize_session=False)

            #  Like削除（親の投稿が相手のものか確認）
            Session.query(Like).filter(
                Like.user_id == user_id,
                Like.post.has(Post.user_id == blocked_user_id)
            ).delete(synchronize_session=False)

            #  SavedPost削除（保存した投稿が相手のものなら削除）
            Session.query(SavedPost).filter(
                SavedPost.user_id == user_id,
                SavedPost.post.has(Post.user_id == blocked_user_id)
            ).delete(synchronize_session=False)

            #  SavedProduct削除（保存した商品が相手のものなら削除）
            Session.query(SavedProduct).filter(
                SavedProduct.user_id == user_id,
                SavedProduct.shop.has(Shop.post.has(Post.user_id == blocked_user_id))
            ).delete(synchronize_session=False)


            # ① ブロックした/された人の投稿に対するリプライを削除
            Session.query(Post).filter(
                Post.reply_id.in_(
                    Session.query(Post.post_id).filter(
                        Post.user_id.in_([user_id, blocked_user_id])
                    )
                )
            ).delete(synchronize_session=False)

            # ② ブロックした/された人が投稿したリプライも削除
            Session.query(Post).filter(
                Post.user_id.in_([user_id, blocked_user_id]),
                Post.reply_id.isnot(None)  # ルート投稿は削除しない
            ).delete(synchronize_session=False)
            
            self.notification_manager.delete_notifications(user_id=user_id,blocked_user_id=blocked_user_id,Session=Session)

            self.make_commit_or_flush(Session)
            return True
        
        except Exception as e:
            self.session_rollback(Session)
            self.app.logger.error(e)
            raise e
from Ganger.app.model.database_manager.database_manager import DatabaseManager
from Ganger.app.model.model_manager import Message,MessageRoom,MessageStatus,RoomMember,User
from sqlalchemy.sql import select,func,exists,desc
from sqlalchemy.orm  import joinedload,aliased
from sqlalchemy.exc import SQLAlchemyError
from flask import current_app as app, session, url_for
from Ganger.app.model.validator import Validator
# import logging
# logging.basicConfig()
# logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)


class MessageManager(DatabaseManager):
    def __init__(self, app=None):
        super().__init__(app)

    def get_or_create_room(self, sender_id, recipient_id, Session=None) -> int:
        """2人のユーザー間のルームを取得、または新規作成する関数"""
        try:
            Session = self.make_session(Session)

            # ルームの既存チェック
            room = Session.query(MessageRoom).filter(
                MessageRoom.room_id.in_(
                    Session.query(RoomMember.room_id)
                    .filter(RoomMember.user_id.in_([sender_id, recipient_id]))
                    .group_by(RoomMember.room_id)
                    .having(func.count(RoomMember.user_id) == 2)
                )
            ).first()


            if room:
                app.logger.info(f"Existing room found: {room.room_id}")
                self.pop_and_close(Session)
                return room.room_id

            # 新規ルーム作成
            room = MessageRoom()
            Session.add(room)
            Session.commit()

            app.logger.info("commit")

            # ルームメンバー追加
            members = [
                RoomMember(room_id=room.room_id, user_id=sender_id),
                RoomMember(room_id=room.room_id, user_id=recipient_id)
            ]
            Session.add_all(members)
            self.make_commit_or_flush(Session)
            app.logger.info(f"Room members added: {members}")

            return room.room_id
        except Exception as e:
            app.logger.error(e)
            self.session_rollback(Session)
            return {"success": False, "message": str(e)}    
        
    def delete_room(self, room_id,Session=None)-> dict:
        """選択されたルームIDを削除するメソッド"""
        try:
            Session = self.make_session(Session)
            dm_room = Session.query(MessageRoom).filter(MessageRoom.room_id == room_id).first()
            app.logger.info(dm_room)
            if not dm_room:
                raise ValueError("DMルームが存在していません。")
            else:
                Session.delete(dm_room)
                self.make_commit_or_flush(Session)
                return {"success":True,"message":"ルームが削除されました。"}
        except ValueError as ve:
            self.session_rollback(Session)
            app.logger.error(ve)
            return {"success":False,"message":str(ve)}
        except Exception as e:
            self.session_rollback(Session)
            app.logger.error(e)
            return {"success":False,"message":str(e)}


    def send_message(self, sender_id, recipient_id, content, Session=None) -> dict:
        """メッセージを送信する関数。ルームがなければ作成する。"""
        try:
            
            Session = self.make_session(Session)
            
            # ルーム取得または新規作成
            room_id = self.get_or_create_room(sender_id, recipient_id)


            # メッセージ挿入
            message = Message(room_id=room_id, sender_id=sender_id, receiver_id=recipient_id, content=content)
            Session.add(message)
            Session.flush()
            app.logger.info(f"Message created: {message}")


            # MessageStatusの挿入 (既読・削除状態の初期化)
            status_sender = MessageStatus(message_id=message.message_id, user_id=sender_id, is_read=True, is_deleted=False)
            status_recipient = MessageStatus(message_id=message.message_id, user_id=recipient_id, is_read=False, is_deleted=False)
            Session.add_all([status_sender, status_recipient])

            self.make_commit_or_flush(Session)

            app.logger.info("Message and statuses committed successfully")
            return {"success": True, "Message": "メッセージ送信成功"}
        except Exception as e:
            app.logger.error(e)
            self.session_rollback(Session)
            return {"success": False, "message": str(e)}
        

    def mark_messages_as_read_up_to(self, message_id, recipient_id, Session=None) -> dict:
        """
        指定されたメッセージIDを含む、それ以前の未読メッセージをすべて既読にする関数。
        """
        try:
            # セッション作成
            Session = self.make_session(Session)
            
            # 対象のメッセージを取得
            message = Session.query(Message).filter(Message.message_id == message_id).first()
            
            if not message:
                raise ValueError("メッセージが存在しません")

            # サブクエリで対象の未読メッセージのステータスIDを取得
            subquery = (
                Session.query(MessageStatus.status_id)
                .join(Message)
                .filter(
                    Message.room_id == message.room_id,
                    Message.sent_time <= message.sent_time,
                    MessageStatus.user_id == recipient_id,
                    MessageStatus.is_read == False
                )
                .subquery()
            )

            # サブクエリの結果に基づいてis_readを更新
            Session.query(MessageStatus).filter(MessageStatus.status_id.in_(select(subquery))).update(
                {"is_read": True}, synchronize_session=False
            )

            self.make_commit_or_flush(Session)
            
            return {"success": True, "message": "メッセージが既読になりました"}
        
        except ValueError as ve:
            app.logger.error(f"ValueError: {ve}")
            self.session_rollback(Session)
            return {"success": False, "message": str(ve)}
        
        except Exception as e:
            app.logger.error(f"Exception: {e}")
            self.session_rollback(Session)
            return {"success": False, "message": str(e)}
        
    def delete_message_for_user(self,message_id, user_id,Session=None):
        """指定されたメッセージを論理削除する関数"""
        try:
            Session = self.make_session(Session)
            status = (
                Session.query(MessageStatus)
                .filter(MessageStatus.message_id == message_id, MessageStatus.user_id == user_id)
                .first()
            )
            if not status:
                raise ValueError("メッセージが存在しません。")
            
            elif status and not status.is_deleted:
                status.is_deleted = True
                self.make_commit_or_flush(Session)
                return {"success":True,"message":"メッセージ削除完了"}
            else:
                return {"success":False,"message":"既に削除されています"}
        except ValueError as ve:
            self.session_rollback(Session)
            app.logger.error(ve)
            return  {"success": False, "message": str(ve)}
        except Exception as e:
            self.session_rollback(Session)
            app.logger.error(e)
            return {"success": False, "message": str(e)}


    def fetch_message_rooms(self, user_id, Session=None) -> dict:
        try:
            Session = self.make_session(Session)
            user_id = Validator.decrypt(user_id)

            # 最新のメッセージを取得するサブクエリ
            latest_message_subquery = (
                Session.query(
                    Message.room_id,
                    func.max(Message.sent_time).label("latest_sent_time")
                )
                .group_by(Message.room_id)
                .subquery()
            )

            # ルームメンバーの「自分以外」のユーザー情報を取得するサブクエリ
            other_user_subquery = (
                Session.query(RoomMember.room_id, User.id, User.username, User.profile_image)
                .join(User, RoomMember.user_id == User.id)
                .filter(RoomMember.user_id != user_id)  # 自分以外のユーザーを取得
                .subquery()
            )

            # クエリ本体
            rooms = (
                Session.query(
                    MessageRoom,
                    Message.content,
                    Message.sent_time,
                    other_user_subquery.c.profile_image,
                    other_user_subquery.c.username
                )
                .join(MessageRoom.room_members)  # 自分のルームを取得
                .join(other_user_subquery, other_user_subquery.c.room_id == MessageRoom.room_id)  # 自分以外のルームメンバー
                .outerjoin(Message, Message.room_id == MessageRoom.room_id)  # メッセージを取得
                .outerjoin(latest_message_subquery, latest_message_subquery.c.room_id == Message.room_id)  # 最新メッセージ取得
                .filter(RoomMember.user_id == user_id)  # 自分が所属するルームのみ取得
                .filter(Message.sent_time == latest_message_subquery.c.latest_sent_time)  # 最新メッセージのみ取得
                .order_by(desc(Message.sent_time))  # 最新メッセージ順
                .all()
            )

            result = []
            for room, last_message, last_sent_time, profile_image, username in rooms:
                result.append({
                    "room_id": Validator.encrypt(room.room_id),
                    "profile_image": url_for("static", filename=f"images/profile_images/{profile_image}") if profile_image else "default-profile.png",
                    "username": username if username else "Unknown",
                    "last_message": last_message if last_message else "",
                    "sent_time": Validator.calculate_time_difference(last_sent_time) if last_sent_time else None
                })
            self.pop_and_close(Session)
            return {"success": True, "result": result}

        except Exception as e:
            self.session_rollback(Session)
            app.logger.error(e)
            return {"success": False, "result": str(e)}
    
    def fetch_messages_by_room(self, room_id, user_id, Session=None):
        """
        `room_id` を使用してメッセージを取得するメソッド。
        - `room_id` 内のメッセージを取得
        - 返却データ:
        - メッセージの `message_id`, `content`, `sent_time`
        - `sender_id` が `user_id` かどうか（`is_self`）
        """
        try:
            Session = self.make_session(Session)

            # `room_id` を使ってメッセージを取得
            messages = (
                Session.query(
                    Message.message_id,
                    Message.content,
                    Message.sent_time,
                    Message.sender_id
                )
                .filter(Message.room_id == room_id)
                .order_by(Message.sent_time.asc())  # 古い順にソート
                .all()
            )

            result = [
                {
                    "message_id": message_id,
                    "content": content,
                    "sent_time": sent_time.isoformat(),
                    "is_self": sender_id == user_id  # 自分の送信かどうか判定
                }
                for message_id, content, sent_time, sender_id in messages
            ]

            self.pop_and_close(Session)
            return {"success": True, "room_id": room_id, "messages": result}

        except Exception as e:
            self.session_rollback(Session)
            return {"success": False, "error": str(e)}
        
    def fetch_messages_by_user(self, user_id, other_user_id, Session=None):
        """
        `user_id` & `other_user_id` を使用してメッセージを取得するメソッド。
        - `user_id` & `other_user_id` のペアで `room_id` を検索
        - ルームが見つからなければ `"No existing room found"` を返す
        - 返却データ:
        - `room_id`
        - 相手の `username`
        - 相手の `profile_image`
        - メッセージの `message_id`, `content`, `sent_time`
        - `sender_id` が `user_id` かどうか（`is_self`）
        """
        try:
            Session = self.make_session(Session)

            # `user_id` & `other_user_id` のペアで `room_id` を検索
            room = (
                Session.query(MessageRoom)
                .join(RoomMember)
                .filter(RoomMember.user_id.in_([user_id, other_user_id]))  # 自分と相手の両方が含まれるルーム
                .group_by(MessageRoom.room_id)
                .having(func.count(RoomMember.user_id) == 2)  # 両方がいるルームのみ
                .first()
            )

            # ルームが見つからない場合はエラーを返す
            if not room:
                return {"success": False, "error": "No existing room found"}

            room_id = room.room_id

            # `room_id` を使ってメッセージと相手の情報を取得
            messages = (
                Session.query(
                    Message.message_id,
                    Message.content,
                    Message.sent_time,
                    Message.sender_id,
                    User.username,
                    User.profile_image
                )
                .join(MessageRoom, Message.room_id == MessageRoom.room_id)  # メッセージルームを取得
                .join(RoomMember, RoomMember.room_id == MessageRoom.room_id)  # ルームメンバーを取得
                .join(User, RoomMember.user_id == User.id)  # メンバーのユーザー情報を取得
                .filter(Message.room_id == room_id)  # `room_id` のメッセージを取得
                .filter(RoomMember.user_id != user_id)  # 自分以外のメンバー（相手）を取得
                .order_by(Message.sent_time.asc())  # 古い順にソート
                .all()
            )

            result = []
            for message_id, content, sent_time, sender_id, username, profile_image in messages:
                result.append({
                    "message_id": message_id,
                    "content": content,
                    "sent_time": sent_time.isoformat(),  # ISOフォーマットで時刻を返す
                    "is_self": sender_id == user_id,  # 自分の送信かどうか判定
                    "username": username,  # 相手の `username`
                    "profile_image": url_for("static", filename=f"images/profile_images/{profile_image}")
                    if profile_image else "default-profile.png"  # プロフィール画像
                })

            self.pop_and_close(Session)
            return {"success": True, "room_id": room_id, "messages": result}

        except Exception as e:
            self.session_rollback(Session)
            return {"success": False, "error": str(e)}

from Ganger.app.model.database_manager.database_manager import DatabaseManager
from Ganger.app.model.model_manager import Message,MessageRoom,MessageStatus,RoomMember,User
from sqlalchemy.sql import select,func,exists,desc,and_
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
            Session.flush()

            app.logger.info("commit")

            # ルームメンバー追加
            members = [
                RoomMember(room_id=room.room_id, user_id=sender_id),
                RoomMember(room_id=room.room_id, user_id=recipient_id)
            ]
            Session.add_all(members)
            self.pop_and_close(Session)
            app.logger.info(f"Room members added: {members}")

            return room.room_id
        except Exception as e:
            app.logger.error(e)
            self.session_rollback(Session)
            raise Exception(str(e))
        
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
            
            #ユーザー主キーの複号化
            sender_id,recipient_id = Validator.decrypt(sender_id),Validator.decrypt(recipient_id)
            # ルーム取得または新規作成
            room_id = self.get_or_create_room(sender_id, recipient_id,Session=Session)


            # メッセージ挿入
            message = Message(room_id=room_id, sender_id=sender_id, receiver_id=recipient_id, content=content)
            Session.add(message)
            Session.flush()
            app.logger.info(f"Message created: {message}")


            # MessageStatusの挿入 (既読・削除状態の初期化)
            status_recipient = MessageStatus(message_id=message.message_id, user_id=recipient_id, is_read=False, is_deleted=False)
            Session.add(status_recipient)

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
            message_id, recipient_id = Validator.decrypt(message_id), Validator.decrypt(recipient_id)
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
            user_id = Validator.decrypt(user_id)
            Session = self.make_session(Session)
            status = (
                Session.query(MessageStatus)
                .filter(MessageStatus.message_id == message_id, MessageStatus.user_id == user_id)
                .first()
            )
            if not status:
                status = MessageStatus(message_id=message_id,user_id=user_id,is_deleted=True)
                Session.add(status)
            
            elif status and not status.is_deleted:
                status.is_deleted = True
            else:
                return {"success":False,"message":"既に削除されています"}
            
            self.make_commit_or_flush(Session)
            return {"success":True,"message":"メッセージ削除完了"}

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
        try:
            Session = self.make_session(Session)
            room_id = Validator.decrypt(room_id)
            user_id = Validator.decrypt(user_id)

            # ルームに参加している相手の情報を取得（自分以外のユーザー）
            other_user = (
                Session.query(User.id, User.username, User.profile_image)
                .join(RoomMember, RoomMember.user_id == User.id)
                .filter(RoomMember.room_id == room_id)
                .filter(RoomMember.user_id != user_id)
                .first()
            )

            if not other_user:
                return {"success": False, "error": "No valid user found in room"}

            # MessageStatus のエイリアスを作成
            read_status = aliased(MessageStatus)
            delete_status = aliased(MessageStatus)

            # `room_id` を使ってメッセージを取得
            messages = (
                Session.query(
                    Message.message_id,
                    Message.content,
                    Message.sent_time,
                    Message.sender_id,
                    func.coalesce(read_status.is_read, False).label("is_read"),
                    func.coalesce(delete_status.is_deleted, False).label("is_deleted")
                )
                .outerjoin(read_status, and_(
                    read_status.message_id == Message.message_id,
                    read_status.user_id == other_user.id
                ))  # 相手の `is_read` を取得
                .outerjoin(delete_status, and_(
                    delete_status.message_id == Message.message_id,
                    delete_status.user_id == user_id
                ))  # 自分の `is_deleted` を取得
                .filter(Message.room_id == room_id)
                .order_by(Message.sent_time.asc())
                .all()
            )

            print("Fetched messages:", messages)  # デバッグ用

            result = [
                {
                    "message_id": Validator.encrypt(message_id),
                    "content": content,
                    "sent_time": Validator.calculate_time_difference(sent_time),
                    "is_me": sender_id == user_id,
                    "status": {
                        "is_read": is_read,
                        "is_deleted": is_deleted
                    }
                }
                for message_id, content, sent_time, sender_id, is_read, is_deleted in messages
            ]

            self.pop_and_close(Session)
            return {
                "success": True,
                "room_id": room_id,
                "user": {
                    "id": Validator.encrypt(other_user.id),
                    "username": other_user.username,
                    "profile_image": url_for("static", filename=f"images/profile_images/{other_user.profile_image}")
                    if other_user.profile_image else "default-profile.png"
                },
                "messages": result
            }

        except Exception as e:
            self.session_rollback(Session)
            return {"success": False, "error": str(e)}

    def fetch_messages_by_user(self, user_id, other_user_id, Session=None):
        try:
            user_id = Validator.decrypt(user_id)
            other_user_id = Validator.decrypt(other_user_id)
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

            room_id = room.room_id if room else None

            # 相手の情報を取得
            other_user = (
                Session.query(User.id, User.username, User.profile_image)
                .filter(User.id == other_user_id)
                .first()
            )

            if not other_user:
                raise ValueError("User not found")

            # **ルームがない場合は `result = []` を設定**
            result = []  

            # `room_id` を使ってメッセージを取得 (ルームがある場合のみ)
            if room_id:
                read_status = aliased(MessageStatus)
                delete_status = aliased(MessageStatus)
                messages = (
                    Session.query(
                        Message.message_id,
                        Message.content,
                        Message.sent_time,
                        Message.sender_id,
                        func.coalesce(read_status.is_read, False).label("is_read"),
                        func.coalesce(delete_status.is_deleted, False).label("is_deleted")
                    )
                    .outerjoin(read_status, and_(
                        read_status.message_id == Message.message_id,
                        read_status.user_id == other_user_id
                    ))  # 相手の `is_read` を取得
                    .outerjoin(delete_status, and_(
                        delete_status.message_id == Message.message_id,
                        delete_status.user_id == user_id
                    ))  # 自分の `is_deleted` を取得
                    .filter(Message.room_id == room_id)
                    .order_by(Message.sent_time.asc())
                    .all()
                )

                result = [
                    {
                        "message_id": Validator.encrypt(message_id),
                        "content": content,
                        "sent_time": Validator.calculate_time_difference(sent_time),
                        "is_me": sender_id == user_id,
                        "status": {
                            "is_read": is_read,
                            "is_deleted": is_deleted
                        }
                    }
                    for message_id, content, sent_time, sender_id, is_read, is_deleted in messages
                ]

            self.pop_and_close(Session)
            return {
                "success": True,
                "room_id": room_id,
                "user": {
                    "id": Validator.encrypt(other_user.id),
                    "username": other_user.username,
                    "profile_image": url_for("static", filename=f"images/profile_images/{other_user.profile_image}")
                    if other_user.profile_image else "default-profile.png"
                },
                "messages": result
            }

        except Exception as e:
            app.logger.error(e)
            self.session_rollback(Session)
            return {"success": False, "error": str(e)}

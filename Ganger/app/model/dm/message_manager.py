from Ganger.app.model.database_manager.database_manager import DatabaseManager
from Ganger.app.model.model_manager import Message,MessageRoom,MessageStatus,RoomMember
from sqlalchemy.sql import select,func,exists
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




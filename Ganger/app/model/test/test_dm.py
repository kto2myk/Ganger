from Ganger.app.model.dm.message_manager import MessageManager
from Ganger.app.model.model_manager import MessageRoom,Message,RoomMember
from sqlalchemy.sql import func
from Ganger.app.view.app import app

with app.test_request_context():
    try:
        dm_manager = MessageManager()
        # result = dm_manager.get_or_create_room(sender_id=1,recipient_id=2)
        # result = dm_manager.delete(model=MessageRoom,filters={"room_id":1})
        result = dm_manager.delete_room(room_id=2)
        # result = dm_manager.send_message(sender_id=1,recipient_id=2,content="aaaaaa")
        # Session = dm_manager.make_session(None)
        # result =    room =Session.query(MessageRoom).filter(
        #             MessageRoom.room_id.in_(
        #                 Session.query(RoomMember.room_id)
        #                 .filter(RoomMember.user_id.in_([13, 14]))
        #                 .group_by(RoomMember.room_id)
        #                 .having(func.count(RoomMember.user_id) == 2)
        #             )
        #         ).first()
        
        print(result)

    except Exception as e:
        print(e)
    # finally:
    #     dm_manager.session_rollback(Session)
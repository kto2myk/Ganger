from Ganger.app.model.dm.message_manager import MessageManager
from Ganger.app.model.model_manager import MessageRoom,Message,RoomMember
from sqlalchemy.sql import func
from Ganger.app.view.app import app

with app.test_request_context():
    try:
        dm_manager = MessageManager()
        # result = dm_manager.get_or_create_room(sender_id=1,recipient_id=2)
        # result = dm_manager.delete(model=MessageRoom,filters={"room_id":1})
        # result = dm_manager.delete_room(room_id=1)
        # result = dm_manager.send_message(sender_id=1,recipient_id=5,content="more status test5")
        result = dm_manager.delete_message_for_user(message_id=1,user_id=1)
        # result = dm_manager.mark_messages_as_read_up_to(message_id=8,recipient_id=5)
                
        print(result)

    except Exception as e:
        print(e)
    # finally:
    #     dm_manager.session_rollback(Session)
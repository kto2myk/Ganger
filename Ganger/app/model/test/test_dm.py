from Ganger.app.model.dm.message_manager import MessageManager
from Ganger.app.view.app import app

with app.test_request_context():
    try:
        dm_manager = MessageManager()
        result = dm_manager.delete_room(room_id=1)
        print(result)

    except Exception as e:
        print(e)

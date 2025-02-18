from Ganger.app.model.dm.message_manager import MessageManager
from Ganger.app.model.model_manager import MessageRoom,Message,RoomMember
from sqlalchemy.sql import func
from Ganger.app.view.app import app
from Ganger.app.model.validator.validate import Validator
with app.test_request_context():
    dm_manager = MessageManager()
    result = dm_manager.fetch_message_rooms(user_id=Validator.encrypt(1))

    print(result['result'])

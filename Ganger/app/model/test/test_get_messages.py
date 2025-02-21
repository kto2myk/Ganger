from Ganger.app.model.dm.message_manager import MessageManager
from Ganger.app.view.app import app
from Ganger.app.model.validator.validate import Validator

with app.test_request_context():
    dm_manager = MessageManager()
    # result = dm_manager.fetch_messages_by_room(user_id=Validator.encrypt(5),
    #                                         room_id=Validator.encrypt(2))
    result = dm_manager.fetch_messages_by_user(user_id=Validator.encrypt(1),other_user_id=Validator.encrypt(5))
    print(result)

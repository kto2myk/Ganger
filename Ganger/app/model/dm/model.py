from Ganger.app.model.database_manager import Base, Column, Integer, ForeignKey, Text, DateTime, func, relationship

class Message(Base):
    __tablename__ = 'messages'
    message_id = Column(Integer, primary_key=True, autoincrement=True)
    sender_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    receiver_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    content = Column(Text, nullable=False)
    sent_time = Column(DateTime, default=func.now())

    sender = relationship("Users", foreign_keys=[sender_id], back_populates="messages_sent")
    receiver = relationship("Users", foreign_keys=[receiver_id], back_populates="messages_received")

    def __repr__(self):
        return f"<Message(message_id={self.message_id}, sender_id={self.sender_id}, receiver_id={self.receiver_id}, sent_time={self.sent_time})>"

class ReadStatus(Base):
    __tablename__ = 'read_statuses'
    status_id = Column(Integer, primary_key=True)
    read_user = Column(Integer, ForeignKey('users.id'), nullable=False)
    message_id = Column(Integer, ForeignKey('messages.message_id'), nullable=False)
    read_time = Column(DateTime)

    read_user = relationship("Users", back_populates="read_statuses")

    def __repr__(self):
        return f"<ReadStatus(status_id={self.status_id}, read_user={self.read_user}, message_id={self.message_id}, read_time={self.read_time})>"

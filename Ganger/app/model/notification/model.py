from Ganger.app.model.database_manager import Base, Column, Integer, String, Text, ForeignKey, DateTime, func, relationship

class Notification(Base):
    __tablename__ = 'notifications'
    notification_id = Column(Integer, primary_key=True, autoincrement=True)
    notification_type = Column(Integer, ForeignKey('notification_types.notification_type_id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    contents = Column(Text, nullable=False)
    sent_time = Column(DateTime, default=func.now())

    user = relationship("Users", back_populates="notifications")

    def __repr__(self):
        return f"<Notification(notification_id={self.notification_id}, user_id={self.user_id}, notification_type={self.notification_type}, sent_time={self.sent_time})>"

class NotificationStatus(Base):
    __tablename__ = 'notification_statuses'
    status_id = Column(Integer, primary_key=True, autoincrement=True)
    notification_id = Column(Integer, ForeignKey('notifications.notification_id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    read = Column(Integer, nullable=False, default=0)
    time_delete = Column(Integer, nullable=False, default=0)

    def __repr__(self):
        return f"<NotificationStatus(status_id={self.status_id}, notification_id={self.notification_id}, user_id={self.user_id}, read={self.read}, time_delete={self.time_delete})>"

class NotificationType(Base):
    __tablename__ = 'notification_types'
    notification_type_id = Column(Integer, primary_key=True, autoincrement=True)
    type_name = Column(String(45), nullable=False)

    def __repr__(self):
        return f"<NotificationType(notification_type_id={self.notification_type_id}, type_name={self.type_name})>"

from Ganger.app.model.database_manager import Base, Column, Integer, String, DateTime, ForeignKey, Date,func, relationship

class User(Base):
    """
    ユーザーを管理するテーブル
    """
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(20), nullable=False, unique=True)
    username = Column(String(16), nullable=False)
    email = Column(String(255), nullable=False, unique=True)
    password = Column(String(20), nullable=False)
    create_time = Column(DateTime, default=func.now())
    real_name = Column(String(45))
    address = Column(String(60))
    birthday = Column(Date, nullable=False)  # 新しい誕生日カラムを追加

    # リレーション
    posts = relationship("Posts", back_populates="author")
    messages_sent = relationship("Messages", foreign_keys="[Messages.sender_id]", back_populates="sender")
    messages_received = relationship("Messages", foreign_keys="[Messages.receiver_id]", back_populates="receiver")
    likes = relationship("Likes", back_populates="user")
    followers = relationship("Follows", foreign_keys="[Follows.user_id]", back_populates="user")
    following = relationship("Follows", foreign_keys="[Follows.follow_user_id]", back_populates="followed_user")
    read_statuses = relationship("ReadStatus", back_populates="read_user")
    notifications = relationship("Notifications", back_populates="user")
    credit_card = relationship("CreditCards", back_populates="user", uselist=False)
    cart = relationship("Carts", back_populates="user")
    saved_posts = relationship("SavePosts", back_populates="user")
    sales = relationship("Sales", back_populates="user")

    def __repr__(self):
        return (f"<User(id={self.id}, user_id={self.user_id}, username={self.username}, "
                f"email={self.email}, create_time={self.create_time}, birthday={self.birthday})>")
    
class Follow(Base):
    """
    フォローテーブル
    """
    __tablename__ = 'follows'

    user_id = Column(Integer, ForeignKey('users.id'), primary_key=True)
    follow_user_id = Column(Integer, ForeignKey('users.id'), primary_key=True)

    # リレーション
    user = relationship("User", foreign_keys=[user_id], back_populates="followers")
    followed_user = relationship("User", foreign_keys=[follow_user_id], back_populates="following")

    def __repr__(self):
        return f"<Follow(user_id={self.user_id}, follow_user_id={self.follow_user_id})>"

class Repost(Base):
    """
    リポストテーブル
    """
    __tablename__ = 'reposts'

    post_id = Column(Integer, ForeignKey('posts.post_id'), primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), primary_key=True)

    def __repr__(self):
        return f"<Repost(post_id={self.post_id}, user_id={self.user_id})>"

class SavePost(Base):
    """
    保存された投稿を管理するテーブル
    """
    __tablename__ = 'save_posts'

    user_id = Column(Integer, ForeignKey('users.id'), primary_key=True)
    post_id = Column(Integer, ForeignKey('posts.post_id'))
    product_id = Column(Integer, ForeignKey('shops.product_id'))

    # リレーション
    user = relationship("User", back_populates="saved_posts")
    post = relationship("Posts", back_populates="saved_posts")

    def __repr__(self):
        return f"<SavePost(user_id={self.user_id}, post_id={self.post_id}, product_id={self.product_id})>"

class Block(Base):
    """
    ブロックされたユーザーを管理するテーブル
    """
    __tablename__ = 'blocks'

    user_id = Column(Integer, ForeignKey('users.id'), primary_key=True)
    blocked_user = Column(Integer, ForeignKey('users.id'), primary_key=True)

    def __repr__(self):
        return f"<Block(user_id={self.user_id}, blocked_user={self.blocked_user})>"

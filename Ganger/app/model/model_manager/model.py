from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean, Numeric, Enum, UniqueConstraint, func
from sqlalchemy.orm import DeclarativeBase, relationship
from datetime import datetime
import pytz

JST = pytz.timezone('Asia/Tokyo')

class Base(DeclarativeBase):    
    pass


# Userテーブル
class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(20), nullable=False, unique=True)
    username = Column(String(16), nullable=False)
    email = Column(String(255), nullable=False, unique=True)
    password = Column(String(255), nullable=False)
    create_time = Column(DateTime, default=lambda: datetime.now(JST))
    real_name = Column(String(45))
    address = Column(String(60))
    bio = Column(String(160)) # プロフィール文
    profile_image = Column(String(255), nullable=False, default="default-profile.png")

    # リレーション
    posts = relationship("Post", back_populates="author") # 投稿
    messages_sent = relationship("Message", foreign_keys="Message.sender_id", back_populates="sender") # 送信メッセージ
    messages_received = relationship("Message", foreign_keys="Message.receiver_id", back_populates="receiver") # 受信メッセージ
    message_statuses = relationship("MessageStatus", back_populates="user", cascade="all, delete-orphan") # MessageStatusとのリレーション
    likes = relationship("Like", back_populates="user") # Likeとのリレーション
    followers = relationship("Follow", foreign_keys="Follow.user_id", back_populates="user") # フォロワー
    following = relationship("Follow", foreign_keys="Follow.follow_user_id", back_populates="followed_user") # フォローしているユーザー
    saved_posts = relationship("SavedPost", back_populates="user", cascade="all, delete-orphan") # SavedPostとのリレーション
    saved_products = relationship("SavedProduct", back_populates="user", cascade="all, delete-orphan") # SavedProductとのリレーション
    blocked_users = relationship("Block", foreign_keys="Block.user_id", back_populates="blocker") # ブロックしたユーザー
    blocked_by = relationship("Block", foreign_keys="Block.blocked_user", back_populates="blocked") # ブロックされたユーザー
    sales = relationship("Sale", back_populates="user") # Saleとのリレーション
    cart = relationship("Cart", back_populates="user") # Cartとのリレーション
    notifications = relationship("Notification", back_populates="user") # Notificationとのリレーション
    notification_statuses = relationship("NotificationStatus", back_populates="user", cascade="all, delete-orphan")  # NotificationStatusとのリレーション
    sent_details = relationship("NotificationDetail", foreign_keys="[NotificationDetail.sender_id]", back_populates="sender")
    received_details = relationship("NotificationDetail", foreign_keys="[NotificationDetail.recipient_id]", back_populates="recipient")
    reposts = relationship("Repost", back_populates="user") # Repostとのリレーション
    rooms = relationship("RoomMember", back_populates="user") # RoomMemberとのリレーション
    def __repr__(self):
            return (f"<User(id={self.id}, user_id={self.user_id}, username={self.username},"
                    f"email={self.email}, create_time={self.create_time}, profile_image={self.profile_image})>") 

class Post(Base):
    __tablename__ = 'posts' # テーブル名

    post_id = Column(Integer, primary_key=True) # 投稿ID
    user_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"), nullable=False) # 投稿者のユーザーID
    body_text = Column(Text, nullable=False) # 投稿本文
    post_time = Column(DateTime, default=lambda: datetime.now(JST)) # 投稿日時
    reply_id = Column(Integer, ForeignKey('posts.post_id', ondelete="SET NULL"), nullable=True) # 返信先の投稿ID

    # リレーション
    shop = relationship("Shop", back_populates="post", uselist=False,cascade="all, delete-orphan")
    author = relationship("User", back_populates="posts") # Userとのリレーション
    images = relationship("Image", back_populates="post", cascade="all, delete-orphan") # Imageとのリレーション
    likes = relationship("Like", back_populates="post", cascade="all, delete-orphan") # Likeとのリレーション
    tags = relationship("TagPost", back_populates="post", cascade="all, delete-orphan") # TagPostとのリレーション
    replies = relationship("Post", backref="parent", remote_side=[post_id],cascade="all") # Postとのリレーション
    reposts = relationship("Repost", back_populates="post",cascade="all, delete-orphan") # Repostとのリレーション
    saved_by_users= relationship("SavedPost", back_populates="post",cascade="all, delete-orphan")  # SavedPostとのリレーション


    
    def __repr__(self):
        return f"<Post(post_id={self.post_id}, user_id={self.user_id}, post_time={self.post_time}, reply_id={self.reply_id})>"


# Followテーブル
class Follow(Base):
    __tablename__ = 'follows'

    user_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"), primary_key=True)
    follow_user_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"), primary_key=True)
    user = relationship("User", foreign_keys=[user_id], back_populates="followers")
    followed_user = relationship("User", foreign_keys=[follow_user_id], back_populates="following")
    created_at = Column(DateTime, default=func.now(), nullable=False)

    def __repr__(self):
        return f"<Follow(user_id={self.user_id}, follow_user_id={self.follow_user_id})>"


# Repostテーブル
class Repost(Base):
    __tablename__ = 'reposts'

    post_id = Column(Integer, ForeignKey('posts.post_id', ondelete="CASCADE"), primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"), primary_key=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    post = relationship("Post", back_populates="reposts")
    user = relationship("User", back_populates="reposts")

    def __repr__(self):
        return f"<Repost(post_id={self.post_id}, user_id={self.user_id})>"


# Blockテーブル
class Block(Base):
    __tablename__ = 'blocks'

    user_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"), primary_key=True)
    blocked_user = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"), primary_key=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    blocker = relationship("User", foreign_keys=[user_id], back_populates="blocked_users")
    blocked = relationship("User", foreign_keys=[blocked_user], back_populates="blocked_by")

    def __repr__(self):
        return f"<Block(user_id={self.user_id}, blocked_user={self.blocked_user})>"


# Imageテーブル
class Image(Base):
    __tablename__ = 'images'

    post_id = Column(Integer, ForeignKey('posts.post_id', ondelete="CASCADE"), primary_key=True, nullable=False)
    img_path = Column(String(255), primary_key=True, nullable=False)
    img_order = Column(Integer, nullable=False)

    __table_args__ = (
        UniqueConstraint('post_id', 'img_order', name='unique_post_image_order'),
    )

    post = relationship("Post", back_populates="images")

    def __repr__(self):
        return f"<Image(post_id={self.post_id}, img_path={self.img_path}, img_order={self.img_order})>"


# Likeテーブル
class Like(Base):
    __tablename__ = 'likes'

    post_id = Column(Integer, ForeignKey('posts.post_id', ondelete="CASCADE"), primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"), primary_key=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    post = relationship("Post", back_populates="likes")
    user = relationship("User", back_populates="likes")

    def __repr__(self):
        return f"<Like(post_id={self.post_id}, user_id={self.user_id})>"


# TagMasterテーブル
class TagMaster(Base):
    __tablename__ = 'tag_master'

    tag_id = Column(Integer, primary_key=True, autoincrement=True)
    tag_text = Column(Text, nullable=False, unique=True)

    def __repr__(self):
        return f"<TagMaster(tag_id={self.tag_id}, tag_text={self.tag_text})>"


# TagPostテーブル
class TagPost(Base):
    __tablename__ = 'tag_posts'

    tag_id = Column(Integer, ForeignKey('tag_master.tag_id', ondelete="CASCADE"), primary_key=True)
    post_id = Column(Integer, ForeignKey('posts.post_id', ondelete="CASCADE"), primary_key=True)

    post = relationship("Post", back_populates="tags")

    def __repr__(self):
        return f"<TagPost(tag_id={self.tag_id}, post_id={self.post_id})>"


# CategoryMasterテーブル
class CategoryMaster(Base):
    __tablename__ = 'category_master'

    category_id = Column(Integer, primary_key=True, autoincrement=True)
    category_name = Column(String(45), nullable=False, unique=True)

    products = relationship("ProductCategory", back_populates="category")

    def __repr__(self):
        return f"<CategoryMaster(category_id={self.category_id}, category_name={self.category_name})>"


# ProductCategoryテーブル
class ProductCategory(Base):
    __tablename__ = 'post_categories'

    category_id = Column(Integer, ForeignKey('category_master.category_id', ondelete="CASCADE"), primary_key=True)
    product_id = Column(Integer, ForeignKey('shops.product_id', ondelete="CASCADE"), primary_key=True)

    product = relationship("Shop", back_populates="categories")
    category = relationship("CategoryMaster", back_populates="products")
    def __repr__(self):
        return f"<ProductCategory(category_id={self.category_id}, product_id={self.product_id})>"


# Shopテーブル
class Shop(Base):
    __tablename__ = 'shops'

    product_id = Column(Integer, primary_key=True, autoincrement=True)
    post_id = Column(Integer, ForeignKey('posts.post_id', ondelete='CASCADE'), nullable=True)
    name = Column(String(45), nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    # リレーション
    post = relationship("Post", back_populates="shop", uselist=False )
    cart_items = relationship("CartItem", back_populates="shop", cascade="all, delete-orphan")
    categories = relationship("ProductCategory", back_populates="product", cascade="all, delete-orphan")
    sales_items = relationship("SalesItem", back_populates="shop", cascade="all, delete-orphan")
    saved_by_users = relationship("SavedProduct", back_populates="shop")  # SavedProductのリレーション

    def __repr__(self):
        return f"<Shop(product_id={self.product_id}, name={self.name}, price={self.price})>"


# Cartテーブル
class Cart(Base):
    __tablename__ = 'carts'

    cart_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(JST))

    user = relationship("User", back_populates="cart")
    cart_items = relationship("CartItem", back_populates="cart", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Cart(cart_id={self.cart_id}, user_id={self.user_id}, created_at={self.created_at})>"


# CartItemテーブル
class CartItem(Base):
    __tablename__ = 'cart_items'

    item_id = Column(Integer, primary_key=True, autoincrement=True)
    cart_id = Column(Integer, ForeignKey('carts.cart_id', ondelete="CASCADE"), nullable=False)
    product_id = Column(Integer, ForeignKey('shops.product_id', ondelete="CASCADE"), nullable=False)
    quantity = Column(Integer, nullable=False)
    added_at = Column(DateTime, default=lambda: datetime.now(JST))

    cart = relationship("Cart", back_populates="cart_items")
    shop = relationship("Shop", back_populates="cart_items")

    def __repr__(self):
        return f"<CartItem(item_id={self.item_id}, cart_id={self.cart_id}, product_id={self.product_id}, quantity={self.quantity})>"


class Sale(Base):
    __tablename__ = 'sales'

    sale_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    total_amount = Column(Numeric(10, 2), nullable=False)
    date = Column(DateTime, default=lambda: datetime.now(JST))
    payment_method = Column(String(50), nullable=False)
    payment_status = Column(Enum('unpaid', 'paid', 'failed', name="payment_status"), default='unpaid')

    user = relationship("User", back_populates="sales")
    items = relationship("SalesItem", back_populates="sale", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Sale(sale_id={self.sale_id}, user_id={self.user_id}, total_amount={self.total_amount}, status={self.status})>"


class SalesItem(Base):
    __tablename__ = 'sales_items'

    sale_item_id = Column(Integer, primary_key=True, autoincrement=True)
    sale_id = Column(Integer, ForeignKey('sales.sale_id', ondelete="CASCADE"), nullable=False)
    product_id = Column(Integer, ForeignKey('shops.product_id', ondelete="CASCADE"), nullable=False)
    quantity = Column(Integer, nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    discount = Column(Numeric(10, 2), default=0.00, nullable=False)
    subtotal = Column(Numeric(10, 2), nullable=False)

    sale = relationship("Sale", back_populates="items")
    shop = relationship("Shop", back_populates="sales_items")

    def __repr__(self):
        return f"<SalesItem(sale_item_id={self.sale_item_id}, sale_id={self.sale_id}, product_id={self.product_id}, quantity={self.quantity})>"

# MessageRoomテーブル
class MessageRoom(Base):
    __tablename__ = 'message_rooms'

    room_id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime, default=lambda: datetime.now(JST))

    room_members = relationship("RoomMember", back_populates="room", cascade="all, delete-orphan")
    messages = relationship("Message", back_populates="room", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<MessageRoom(room_id={self.room_id}, created_at={self.created_at})>"


# RoomMemberテーブル
class RoomMember(Base):
    __tablename__ = 'room_members'

    room_id = Column(Integer, ForeignKey('message_rooms.room_id', ondelete='CASCADE'), primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)

    user = relationship("User", back_populates="rooms")
    room = relationship("MessageRoom", back_populates="room_members")

    def __repr__(self):
        return f"<RoomMember(room_id={self.room_id}, user_id={self.user_id})>"


# Messageテーブル
class Message(Base):
    __tablename__ = 'messages'

    message_id = Column(Integer, primary_key=True, autoincrement=True)
    room_id = Column(Integer, ForeignKey('message_rooms.room_id', ondelete='CASCADE'), nullable=False)
    sender_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    receiver_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    content = Column(Text, nullable=False)
    sent_time = Column(DateTime, default=lambda: datetime.now(JST))

    # リレーション
    room = relationship("MessageRoom", back_populates="messages")
    sender = relationship("User", foreign_keys=[sender_id], back_populates="messages_sent")
    receiver = relationship("User", foreign_keys=[receiver_id], back_populates="messages_received")
    statuses = relationship("MessageStatus", back_populates="message", cascade="all, delete-orphan")  # MessageStatusとのリレーション

    def __repr__(self):
        return (f"<Message(message_id={self.message_id}, sender_id={self.sender_id}, "
                f"receiver_id={self.receiver_id}, sent_time={self.sent_time})>")
    
# MessageStatusテーブル
class MessageStatus(Base):
    __tablename__ = 'message_statuses'

    status_id = Column(Integer, primary_key=True, autoincrement=True)
    message_id = Column(Integer, ForeignKey('messages.message_id', ondelete='CASCADE'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    is_read = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False)

    message = relationship("Message", back_populates="statuses")
    user = relationship("User", back_populates="message_statuses")

    def __repr__(self):
        return (f"<MessageStatus(status_id={self.status_id}, message_id={self.message_id}, "
                f"user_id={self.user_id}, is_read={self.is_read}, is_deleted={self.is_deleted})>")

# Notificationテーブル
class Notification(Base):
    __tablename__ = 'notifications'

    notification_id = Column(Integer, primary_key=True, autoincrement=True)
    notification_type_id = Column(Integer, ForeignKey('notification_types.notification_type_id', ondelete='CASCADE'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    contents = Column(Text, nullable=False)
    sent_time = Column(DateTime, default=lambda: datetime.now(JST))

    # リレーション
    user = relationship("User", back_populates="notifications")
    notification_type_relation = relationship("NotificationType", back_populates="notifications")
    statuses = relationship("NotificationStatus", back_populates="notification", cascade="all, delete-orphan") 
    details = relationship("NotificationDetail", back_populates="notification", cascade="all, delete-orphan")
    def __repr__(self):
        return (f"<Notification(notification_id={self.notification_id}, user_id={self.user_id}, "
                f"notification_type_id={self.notification_type_id}, sent_time={self.sent_time})>")


# NotificationStatusテーブル
class NotificationStatus(Base):
    __tablename__ = 'notification_statuses'

    status_id = Column(Integer, primary_key=True, autoincrement=True)
    notification_id = Column(Integer, ForeignKey('notifications.notification_id', ondelete='CASCADE'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)  # Userとのリレーション
    is_read = Column(Boolean, nullable=False, default=False)
    is_deleted = Column(Boolean, nullable=False, default=False)

    # リレーション
    notification = relationship("Notification", back_populates="statuses")
    user = relationship("User", back_populates="notification_statuses")  # Userとのリレーション

    def __repr__(self):
        return (f"<NotificationStatus(status_id={self.status_id}, notification_id={self.notification_id}, "
                f"user_id={self.user_id}, is_read={self.is_read}, is_deleted={self.is_deleted})>")


# NotificationTypeテーブル
class NotificationType(Base):
    __tablename__ = 'notification_types'

    notification_type_id = Column(Integer, primary_key=True, autoincrement=True)
    type_name = Column(String(45), nullable=False, unique=True)

    notifications = relationship("Notification", back_populates="notification_type_relation", cascade="all, delete-orphan")
    details = relationship("NotificationDetail", back_populates="notification_type", cascade="all, delete-orphan")
    def __repr__(self):
        return f"<NotificationType(notification_type_id={self.notification_type_id}, type_name={self.type_name})>"

class NotificationDetail(Base):
    __tablename__ = 'notification_details'

    detail_id = Column(Integer, primary_key=True, autoincrement=True)
    notification_id = Column(Integer, ForeignKey('notifications.notification_id', ondelete='CASCADE'), nullable=False)
    sender_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    recipient_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    notification_type_id = Column(Integer, ForeignKey('notification_types.notification_type_id', ondelete='CASCADE'), nullable=False)
    related_item_id = Column(Integer, nullable=True)  # 関連項目（例: PostID, CartID）
    related_item_type = Column(String(50), nullable=True)  # 関連項目の種類（例: "post", "cart"）
    created_at = Column(DateTime, default=lambda: datetime.now(JST))

    # リレーション
    notification = relationship("Notification", back_populates="details")
    sender = relationship("User", foreign_keys=[sender_id], back_populates="sent_details")
    recipient = relationship("User", foreign_keys=[recipient_id], back_populates="received_details")
    notification_type = relationship("NotificationType", back_populates="details")

    def __repr__(self):
        return (f"<NotificationDetail(detail_id={self.detail_id}, notification_id={self.notification_id}, "
                f"sender_id={self.sender_id}, recipient_id={self.recipient_id}, "
                f"related_item_id={self.related_item_id}, related_item_type={self.related_item_type})>")
    
# 保存された投稿
class SavedPost(Base):
    __tablename__ = 'saved_posts'

    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
    post_id = Column(Integer, ForeignKey('posts.post_id', ondelete='CASCADE'), primary_key=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)  # 保存日時を追加

    user = relationship("User", back_populates="saved_posts")
    post = relationship("Post", back_populates="saved_by_users")

# 保存された商品
class SavedProduct(Base):
    __tablename__ = 'saved_products'

    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
    product_id = Column(Integer, ForeignKey('shops.product_id', ondelete='CASCADE'), primary_key=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)  # 保存日時を追加

    user = relationship("User", back_populates="saved_products")
    shop = relationship("Shop", back_populates="saved_by_users")

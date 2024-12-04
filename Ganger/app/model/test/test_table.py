from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import date
from Ganger.app.model.model_manager import Base, User, Post, Follow, Repost, Block, Image, Like, TagMaster, TagPost, \
    CategoryMaster, PostCategory, Shop, Cart, CartItem, Sale, SalesItem, MessageRoom, RoomMember, Message, \
    MessageStatus, Notification, NotificationType, NotificationStatus, SavePost
from sqlalchemy.orm import mapperlib

# SQLiteの絶対パス
DATABASE_URL = r"sqlite:///C:\HAL\IH\IH22\Ganger\app\model\database_manager\Ganger.db"

# エンジン作成
engine = create_engine(DATABASE_URL, echo=True)
# セッションの作成
Session = sessionmaker(bind=engine)
session = Session()

# テストデータの挿入
try:
    # ユーザーデータ
    user1 = User(user_id="user1", username="Alice", email="alice@example.com", password="password1", birthday=date(1985, 5, 15))
    user2 = User(user_id="user2", username="Bob", email="bob@example.com", password="password2", birthday=date(1990, 1, 1))
    session.add_all([user1, user2])
    session.commit()

    # 投稿データ
    post1 = Post(user_id=user1.id, body_text="Hello World!", reply_id=None)
    post2 = Post(user_id=user2.id, body_text="This is a reply.", reply_id=post1.post_id)
    session.add_all([post1, post2])
    session.commit()

    # フォロー関係
    follow1 = Follow(user_id=user1.id, follow_user_id=user2.id)
    session.add(follow1)
    session.commit()

    # リポスト
    repost1 = Repost(post_id=post1.post_id, user_id=user2.id)
    session.add(repost1)
    session.commit()

    # ブロック
    block1 = Block(user_id=user1.id, blocked_user=user2.id)
    session.add(block1)
    session.commit()

    # イメージデータ
    image1 = Image(post_id=post1.post_id, img_path="path/to/image1.jpg", img_order=1)
    session.add(image1)
    session.commit()

    # いいねデータ
    like1 = Like(post_id=post1.post_id, user_id=user2.id)
    session.add(like1)
    session.commit()

    # タグとカテゴリー
    tag = TagMaster(tag_text="TestTag")
    category = CategoryMaster(category_name="TestCategory")
    session.add_all([tag, category])
    session.commit()

    tag_post = TagPost(tag_id=tag.tag_id, post_id=post1.post_id)
    post_category = PostCategory(category_id=category.category_id, post_id=post1.post_id)
    session.add_all([tag_post, post_category])
    session.commit()

    # ショップデータ
    shop_item = Shop(name="Test Product", price=19.99, post_id=post1.post_id)
    session.add(shop_item)
    session.commit()

    # カートデータ
    cart = Cart(user_id=user1.id)
    session.add(cart)
    session.commit()

    cart_item = CartItem(cart_id=cart.cart_id, product_id=shop_item.product_id, quantity=2)
    session.add(cart_item)
    session.commit()

    # セールデータ
    sale = Sale(user_id=user1.id, total_amount=39.98)
    session.add(sale)
    session.commit()

    sales_item = SalesItem(sale_id=sale.sale_id, product_id=shop_item.product_id, quantity=2, price=19.99)
    session.add(sales_item)
    session.commit()

    # メッセージデータ
    room = MessageRoom()
    session.add(room)
    session.commit()

    room_member1 = RoomMember(room_id=room.room_id, user_id=user1.id)
    room_member2 = RoomMember(room_id=room.room_id, user_id=user2.id)
    session.add_all([room_member1, room_member2])
    session.commit()

    message = Message(room_id=room.room_id, sender_id=user1.id, receiver_id=user2.id, content="Hello!")
    session.add(message)
    session.commit()

    # 通知データ
    notification_type = NotificationType(type_name="General")
    session.add(notification_type)
    session.commit()

    notification = Notification(notification_type_id=notification_type.notification_type_id, user_id=user2.id, contents="Test Notification")
    session.add(notification)
    session.commit()

    print("テストデータの挿入が完了しました！")

except Exception as e:
    session.rollback()
    print(f"エラーが発生しました: {e}")


finally:
    session.close()

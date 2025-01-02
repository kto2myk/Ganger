from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from Ganger.app.model.model_manager import Base, User, Post, Follow, Repost, Block, Image, Like, TagMaster, TagPost, \
    CategoryMaster, ProductCategory, Shop, Cart, CartItem, Sale, SalesItem, MessageRoom, RoomMember, Message, \
    MessageStatus, Notification, NotificationType

# SQLiteの絶対パス
DATABASE_URL = r"sqlite:///C:\HAL\IH\IH22\Ganger\app\model\database_manager\Ganger.db"

# エンジン作成
engine = create_engine(DATABASE_URL, echo=True)
# セッションの作成
Session = sessionmaker(bind=engine)
session = Session()

# --- テストデータ挿入開始 ---
try:
    # ユーザーデータ
    user1 = User(user_id="user1", username="Alice", email="alice@example.com", password="password1")
    user2 = User(user_id="user2", username="Bob", email="bob@example.com", password="password2")
    session.add_all([user1, user2])
    session.commit()

    # 投稿データ
    post1 = Post(user_id=user1.id, body_text="Hello World!")
    post2 = Post(user_id=user2.id, body_text="Replying to the first post.", reply_id=None)
    session.add_all([post1, post2])
    session.commit()

    # フォロー関係
    follow = Follow(user_id=user1.id, follow_user_id=user2.id)
    session.add(follow)
    session.commit()

    # リポストデータ
    repost = Repost(post_id=post1.post_id, user_id=user2.id)
    session.add(repost)
    session.commit()

    # ブロックデータ
    block = Block(user_id=user1.id, blocked_user=user2.id)
    session.add(block)
    session.commit()

    # 画像データ
    image = Image(post_id=post1.post_id, img_path="images/post1.jpg", img_order=1)
    session.add(image)
    session.commit()

    # いいねデータ
    like = Like(post_id=post1.post_id, user_id=user2.id)
    session.add(like)
    session.commit()

    # タグとカテゴリー
    tag = TagMaster(tag_text="GeneralTag")
    category = CategoryMaster(category_name="Books")
    session.add_all([tag, category])
    session.commit()

    # タグポストと商品カテゴリ
    tag_post = TagPost(tag_id=tag.tag_id, post_id=post1.post_id)
    product_category = ProductCategory(category_id=category.category_id, product_id=post1.post_id)
    session.add_all([tag_post, product_category])
    session.commit()

    # ショップデータ
    shop_item = Shop(name="Book", price=9.99, post_id=post1.post_id)
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
    sale = Sale(user_id=user1.id, total_amount=19.98)
    session.add(sale)
    session.commit()

    sales_item = SalesItem(sale_id=sale.sale_id, product_id=shop_item.product_id, quantity=2, price=9.99)
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

    message = Message(room_id=room.room_id, sender_id=user1.id, receiver_id=user2.id, content="Hello, Bob!")
    session.add(message)
    session.commit()

    # 通知データ
    notification_type = NotificationType(type_name="Info")
    session.add(notification_type)
    session.commit()

    notification = Notification(notification_type_id=notification_type.notification_type_id, user_id=user2.id, contents="New notification")
    session.add(notification)
    session.commit()

    print("テストデータの挿入が完了しました！")

except Exception as e:
    session.rollback()
    print(f"エラーが発生しました: {e}")

finally:
    session.close()

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from Ganger.app.model.model_manager.model import Base, User, Post, Follow, Notification, NotificationType, Shop, Cart, CartItem

# テスト用データベースを設定
TEST_DB_URL = "sqlite:///:memory:"  # メモリ内データベースを使用

@pytest.fixture(scope="module")
def test_session():
    """テスト用のSQLAlchemyセッションを準備"""
    engine = create_engine(TEST_DB_URL)
    Base.metadata.create_all(engine)  # テーブル作成
    Session = sessionmaker(bind=engine)
    session = Session()

    yield session

    session.close()
    Base.metadata.drop_all(engine)  # テスト終了時にテーブルを削除


def test_add_user(test_session):
    """Userテーブルへのデータ追加"""
    user = User(
        user_id="test_user",
        username="TestUser",
        email="test@example.com",
        password="hashed_password",
    )
    test_session.add(user)
    test_session.commit()

    # データが正しく追加されたか確認
    assert test_session.query(User).count() == 1


def test_add_post(test_session):
    """Postテーブルへのデータ追加"""
    user = test_session.query(User).first()
    post = Post(
        user_id=user.id,
        body_text="This is a test post."
    )
    test_session.add(post)
    test_session.commit()

    # データが正しく追加されたか確認
    assert test_session.query(Post).count() == 1


def test_add_follow(test_session):
    """Followテーブルへのデータ追加"""
    user1 = User(
        user_id="user1",
        username="User1",
        email="user1@example.com",
        password="hashed_password",
        birthday="1995-01-01"
    )
    user2 = User(
        user_id="user2",
        username="User2",
        email="user2@example.com",
        password="hashed_password",
        birthday="1998-01-01"
    )
    test_session.add_all([user1, user2])
    test_session.commit()

    follow = Follow(user_id=user1.id, follow_user_id=user2.id)
    test_session.add(follow)
    test_session.commit()

    # データが正しく追加されたか確認
    assert test_session.query(Follow).count() == 1


def test_add_notification(test_session):
    """Notificationテーブルへのデータ追加"""
    notification_type = NotificationType(notification_type_id=1, type_name="General")
    test_session.add(notification_type)
    test_session.commit()

    user = test_session.query(User).first()
    notification = Notification(user_id=user.id, contents="Test Notification", notification_type_id=1)
    test_session.add(notification)
    test_session.commit()

    # データが正しく追加されたか確認
    assert test_session.query(Notification).count() == 1


def test_add_cart_item(test_session):
    """CartItemテーブルへのデータ追加"""
    user = test_session.query(User).first()
    shop = Shop(name="Test Product", price=100.0)
    cart = Cart(user_id=user.id)
    cart_item = CartItem(cart=cart, shop=shop, quantity=1)

    test_session.add_all([shop, cart, cart_item])
    test_session.commit()

    # データが正しく追加されたか確認
    assert test_session.query(CartItem).count() == 1

from Ganger.app.model.database_manager import Base, Column, Integer, String, DECIMAL, DateTime, ForeignKey, func, relationship

class Shop(Base):
    """
    商品情報を管理するテーブル
    """
    __tablename__ = 'shops'
    product_id = Column(Integer, primary_key=True, autoincrement=True)
    post_id = Column(Integer, ForeignKey('posts.post_id'), nullable=False)  # 関連する投稿
    tag_id = Column(Integer, ForeignKey('tag_master.tag_id'), nullable=False)  # 関連するタグ
    category_id = Column(Integer, ForeignKey('category_master.category_id'), nullable=False)  # 関連するカテゴリ
    name = Column(String(45), nullable=False)  # 商品名
    price = Column(DECIMAL(10, 2), nullable=False)  # 商品価格

    cart = relationship("Carts", back_populates="items")  # カートに関連付け

    def __repr__(self):
        return f"<Shop(product_id={self.product_id}, name={self.name}, price={self.price})>"

class Sale(Base):
    """
    売上情報を管理するテーブル
    """
    __tablename__ = 'sales'
    sale_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)  # 購入者
    total_amount = Column(DECIMAL(10, 2), nullable=False)  # 合計金額
    date = Column(DateTime, default=func.now())  # 購入日時

    user = relationship("Users", back_populates="sales")  # ユーザーとのリレーション
    items = relationship("SalesItems", back_populates="sale")  # 売上アイテムとのリレーション

    def __repr__(self):
        return f"<Sale(sale_id={self.sale_id}, user_id={self.user_id}, total_amount={self.total_amount}, date={self.date})>"

class SalesItem(Base):
    """
    売上アイテムを管理するテーブル
    """
    __tablename__ = 'sales_items'
    sale_item_id = Column(Integer, primary_key=True, autoincrement=True)
    sale_id = Column(Integer, ForeignKey('sales.sale_id'), nullable=False)  # 関連する売上
    product_id = Column(Integer, ForeignKey('shops.product_id'), nullable=False)  # 購入された商品
    quantity = Column(Integer, nullable=False)  # 購入数量
    price = Column(DECIMAL(10, 2), nullable=False)  # 購入価格

    sale = relationship("Sales", back_populates="items")  # 売上とのリレーション

    def __repr__(self):
        return f"<SalesItem(sale_item_id={self.sale_item_id}, sale_id={self.sale_id}, product_id={self.product_id}, quantity={self.quantity}, price={self.price})>"

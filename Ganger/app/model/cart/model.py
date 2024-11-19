from Ganger.app.model.database_manager import Base, Column, Integer, ForeignKey, DateTime, func, relationship

class Cart(Base):
    __tablename__ = 'carts'
    cart_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('shops.product_id'), nullable=False)
    time = Column(DateTime, default=func.now())

    user = relationship("Users", back_populates="cart")
    items = relationship("CartItems", back_populates="cart")

    def __repr__(self):
        return f"<Cart(cart_id={self.cart_id}, user_id={self.user_id}, product_id={self.product_id}, time={self.time})>"

class CartItem(Base):
    __tablename__ = 'cart_items'
    item_id = Column(Integer, primary_key=True, autoincrement=True)
    cart_id = Column(Integer, ForeignKey('carts.cart_id'), nullable=False)
    product_id = Column(Integer, ForeignKey('shops.product_id'), nullable=False)
    quantity = Column(Integer, nullable=False)

    def __repr__(self):
        return f"<CartItem(item_id={self.item_id}, cart_id={self.cart_id}, product_id={self.product_id}, quantity={self.quantity})>"
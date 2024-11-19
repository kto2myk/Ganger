from Ganger.app.model.database_manager import Base, Column, Integer, String, DateTime, ForeignKey, relationship

class CreditCard(Base):
    __tablename__ = 'credit_cards'
    user_id = Column(Integer, ForeignKey('users.id'), primary_key=True)
    credit_number = Column(String(16), nullable=False)
    credit_limit = Column(DateTime, nullable=False)
    credit_code = Column(String(4), nullable=False)

    user = relationship("Users", back_populates="credit_card")

    def __repr__(self):
        return f"<CreditCard(user_id={self.user_id}, credit_number='**** **** **** {self.credit_number[-4:]}', credit_limit={self.credit_limit})>"

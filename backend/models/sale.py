from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from backend.database import Base


class Sale(Base):
    __tablename__ = "sales"

    id = Column(Integer, primary_key=True, index=True)
    invoice_no = Column(String(64), unique=True, index=True, nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="SET NULL"), nullable=True, index=True)

    # Financial details
    subtotal = Column(Numeric(10, 2), nullable=False, default=0.00)
    discount = Column(Numeric(10, 2), nullable=False, default=0.00)
    tax = Column(Numeric(10, 2), nullable=False, default=0.00)
    total_amount = Column(Numeric(10, 2), nullable=False, default=0.00)

    # Payment & status (Cash, Card, Digital Transfer)
    payment_method = Column(String(50), nullable=False, default="Cash")
    status = Column(String(30), nullable=False, default="COMPLETED")  # COMPLETED, CANCELLED, REFUNDED
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    # Relationships
    customer = relationship("Customer", back_populates="sales")
    items = relationship("SaleItem", back_populates="sale", cascade="all, delete-orphan", lazy="joined")

    def __repr__(self):
        return f"<Sale(id={self.id}, invoice='{self.invoice_no}', total={self.total_amount})>"


class SaleItem(Base):
    __tablename__ = "sale_items"

    id = Column(Integer, primary_key=True, index=True)
    sale_id = Column(Integer, ForeignKey("sales.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True)

    quantity = Column(Integer, nullable=False, default=1)
    unit_price = Column(Numeric(10, 2), nullable=False, default=0.00)
    cost_price = Column(Numeric(10, 2), nullable=False, default=0.00)  # Saved at time of sale for accurate profit margin
    subtotal = Column(Numeric(10, 2), nullable=False, default=0.00)

    # Relationships
    sale = relationship("Sale", back_populates="items")
    product = relationship("Product", back_populates="sale_items", lazy="joined")

    def __repr__(self):
        return f"<SaleItem(id={self.id}, product_id={self.product_id}, qty={self.quantity}, subtotal={self.subtotal})>"

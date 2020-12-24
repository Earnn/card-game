from sqlalchemy import Boolean, Column, ForeignKey, Numeric, Integer, String
from sqlalchemy.orm import relationship

from db import Base

class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(500), index=True)
    last_name = Column(String(500), index=True)
    phone_number = Column(String(10), index=True)

    game_state = relationship("CustomerGameState", back_populates="customer")

class CustomerGameState(Base):
    __tablename__ = "customer_game_states"

    id = Column(Integer, primary_key=True, index=True)
    current_state = Column(String(255), index=True)
    my_best = Column(Integer)
    customer_id = Column(Integer, ForeignKey("customers.id"))

    customer = relationship("Customer", back_populates="game_state")


class GlobalGameState(Base):
    __tablename__ = "global_game_states"

    id = Column(Integer, primary_key=True, index=True)
    state = Column(String(255), index=True)
    global_best = Column(Integer)

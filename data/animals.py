from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from .db_session import SqlAlchemyBase


class Animal(SqlAlchemyBase):
    __tablename__ = 'animals'
    id = Column(Integer, primary_key=True)
    mode = Column(String)
    name = Column(String)
    oset_name = Column(String)
    additional_parameters = Column(String)

    mode_one = relationship("ModeOne", back_populates="animal")
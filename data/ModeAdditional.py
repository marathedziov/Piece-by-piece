from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from .db_session import SqlAlchemyBase


class ModeAdditional(SqlAlchemyBase):
    __tablename__ = 'mode_additional'
    id = Column(Integer, primary_key=True)
    id_animal = Column(Integer, ForeignKey('animals.id'))
    tasks = Column(String)
    answers = Column(String)
    png = Column(String)

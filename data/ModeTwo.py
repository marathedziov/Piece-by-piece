from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from .db_session import SqlAlchemyBase


class ModeTwo(SqlAlchemyBase):
    __tablename__ = 'mode_two'
    id = Column(Integer, primary_key=True)
    id_animal = Column(Integer, ForeignKey('animals.id'))
    mp3 = Column(String)
    png = Column(String)
    answer = Column(String)
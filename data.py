from typing import List
from sqlalchemy import String, Table, Column, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass

class HotelType(Base):
    # {'经济型', '舒适型', '豪华型', '高档型'}
    __tablename__ = "hotel_type"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(2), unique=True)
    hotels: Mapped[List["Hotel"]] = relationship(
        back_populates="hotel_type", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return self.name

class Subway(Base):
    __tablename__ = "subway"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(5), unique=True)   
    hotels: Mapped[List["Hotel"]] = relationship(
        back_populates="subway", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return self.name

hotel_fac_table = Table(
    "hotel_fac",
    Base.metadata,
    Column("hotel_id", ForeignKey("hotel.id")),
    Column("fac_id", ForeignKey("fac_type.id")),
)

class FacType(Base):
    __tablename__ = "fac_type"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(9), unique=True) 
    hotels: Mapped[List["Hotel"]] = relationship(secondary=hotel_fac_table, back_populates="facs")

    def __repr__(self):
        return self.name

class Hotel(Base):
    __tablename__ = "hotel"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(9), unique=True)
    address: Mapped[str] = mapped_column(String(127))
    phone: Mapped[str] = mapped_column(String(11))
    price: Mapped[float]
    rating: Mapped[float]
    type_id: Mapped[int] = mapped_column(ForeignKey("hotel_type.id"))
    hotel_type: Mapped[HotelType] = relationship(back_populates="hotels")
    subway_id: Mapped[int] = mapped_column(ForeignKey("subway.id"))
    subway: Mapped[Subway] = relationship(back_populates="hotels")
    facs: Mapped[List[FacType]] = relationship(secondary=hotel_fac_table, back_populates="hotels")

    def to_json(self):
        return {
            'name': self.name,
            'address': self.address,
            'phone': self.phone,
            'price': self.price,
            'rating': self.rating,
            'hotel_type': self.hotel_type,
            'subway': self.subway,
            'facilities': self.facs
        }
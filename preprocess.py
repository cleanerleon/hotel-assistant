import json
import re
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from data import Base, HotelType, Subway, FacType, Hotel

hotel_path = r"hotel-data/hotel.json"


def get_hotel_data():
    with open(hotel_path, "r") as f:
        return json.load(f)


def gen_hotel_db():
    hotel_types = dict()
    subways = dict()
    facilities = dict()
    hotels = []
    ptn = r"(\w+)地铁站"
    hotel_data = get_hotel_data()
    for hotel_item in hotel_data:
        type_name = hotel_item["type"]
        hotel_type = hotel_types.get(type_name)
        if hotel_type is None:
            hotel_type = HotelType(name=type_name)
            hotel_types[type_name] = hotel_type

        subway = hotel_item["subway"]
        m = re.search(ptn, subway)
        if m is None:
            raise Exception("Unknown subway")
        name = m.group(1) + "地铁站"
        subway = subways.get(name)
        if subway is None:
            subway = Subway(name=name)
            subways[name] = subway

        facility = hotel_item["facilities"]
        seps = facility.split(":")
        if seps[0] != "酒店提供的设施":
            raise Exception("Unknown facility")
        items = seps[1].split(";")
        items = [item for item in items if item.strip() != ""]
        # extra_items = []
        facs = []
        for item in items:
            # if item == '公共区域和部分房间提供wifi':
            #     extra_items.extend(['公共区域提供wifi', '部分房间提供wifi'])
            #     continue
            # if item == '酒店各处提供wifi':
            #     extra_items.extend(['公共区域提供wifi', '所有房间提供wifi'])
            #     continue
            fac = facilities.get(item)
            if fac is None:
                fac = FacType(name=item)
                facilities[item] = fac
            facs.append(fac)
        # for item in extra_items:
        #     fac = facilities.get(item)
        #     if fac is None:
        #         fac = FacType(name=item)
        #         facilities[item] = fac
        #     facs.append(fac)
        print(facs)
        item = hotel_item
        hotel = Hotel(
            name=item["name"],
            hotel_type=hotel_type,
            address=item["address"],
            subway=subway,
            phone=item["phone"],
            facs=facs,
            price=item["price"],
            rating=item["rating"],
        )
        hotels.append(hotel)

    engine = create_engine("sqlite:///hotel.db", echo=False)
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        session.add_all(hotels)
        session.commit()


if __name__ == "__main__":
    gen_hotel_db()

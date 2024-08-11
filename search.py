import dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
# from sqlalchemy import or_
# from langchain_core.tools import tool
# from langchain_openai import ChatOpenAI
from consts import fac_types, hotel_types, subway_names
from data import Hotel

dotenv.load_dotenv('env.conf')
# llm = ChatOpenAI(model="gpt-4o")  # 默认是gpt-3.5-turbo
# response = llm.invoke("你是谁")
# print(response.content)

# @tool
def find_hotel(session, htype=None, rating_low=None, rating_hi=None, price_low=None, price_hi=None, subway=None, facilities=None):
    if htype not in hotel_types:
        htype = None
    if facilities:
        facilities = [item for item in facilities if item in fac_types]
    if subway not in subway_names:
        subway = None

    filters = []
    if htype:
        filters.append(Hotel.hotel_type == htype)
    if facilities:
        filters.append(Hotel.facs == facilities)
    if rating_low:
        filters.append(Hotel.rating >= rating_low)
    if rating_hi:
        filters.append(Hotel.rating <= rating_hi)
    if price_low:
        filters.append(Hotel.price >= price_low)
    if price_hi:
        filters.append(Hotel.price >= price_hi)
    if subway:
        filters.append(Hotel.subway == subway)
    if filters:
        res = session.query(Hotel).filter(filters).all()
    else:
        res = session.query(Hotel).all()
    for item in res:
        print(item.to_json())

if __name__ == '__main__':
    engine = create_engine("sqlite:///hotel.db", echo=False)
    with Session(engine) as session:
        find_hotel(session)
from typing import List, Union, Optional
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy import or_
from sqlalchemy import select
import dotenv

from langchain_core.tools import tool
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.chat_history import (
    BaseChatMessageHistory,
    InMemoryChatMessageHistory,
)
from langchain_core.messages import HumanMessage, ToolMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI

from consts import fac_types, hotel_types, subway_names, system_prompt
from data import Hotel, HotelType, FacType, hotel_fac_table

dotenv.load_dotenv("env.conf")


def check_facilites(result, facilities):
    for item in result:
        match = 0
        for fac in facilities:
            if type(fac) is str:
                for fac_item in item.facs:
                    if fac_item.name == fac:
                        match += 1
            else:
                found = False
                for check_item in fac:
                    for fac_item in item.facs:
                        if fac_item.name == check_item:
                            match += 1
                            found = True
                            break
                    if found:
                        break
        if match != len(facilities):
            print("faciity error")

@tool
def find_hotel(
    htype: Optional[str] = None,
    rating_low: Optional[float] = None,
    rating_hi: Optional[float] = None,
    price_low: Optional[float] = None,
    price_hi: Optional[float] = None,
    subway: Optional[str] = None,
    facilities: Optional[List[Union[str, List[str]]]] = None,
):
    """
    根据用户的要求在数据库中搜索符合要求的酒店
    htype是字符串，表示酒店的档次，取值范围是'高档型', '舒适型', '经济型', '豪华型'
    rating_low是浮点数，是酒店评分的最低值
    rating_hi是浮点数，是酒店评分的最高值
    price_low是浮点数，是酒店价格的最低值
    price_hi是浮点数，是酒店价格的最高值
    subway是字符串，表示附近的地铁站，取值范围是北京地铁站名
    facilities是数组，表示酒店设施，取值范围在'健身房', '暖气', '行李寄存', '无烟房', 'SPA', '公共区域和部分房间提供wifi', '部分房间提供wifi', '早餐服务免费', '商务中心', '酒店各处提供wifi', '所有房间提供wifi', '早餐服务', '温泉', '接站服务', '接机服务', '吹风机', '中式餐厅', '24小时热水', '宽带上网', '租车', '室外游泳池', '会议室', '接待外宾', '国际长途电话', '收费停车位', '桑拿', '公共区域提供wifi', '残疾人设施', '室内游泳池', '叫醒服务', '免费国内长途电话', '免费市内电话', '西式餐厅', '洗衣服务', '棋牌室', '酒吧', '看护小孩服务'；数组元素之间是与的关系，如果是或的关系，用数组表示，如表示带健身房或者带暖气，参数值为[['健身房', '暖气']]，表示带健身房和暖气，参数值为['健身房', '暖气']，如用户想查找带WIFI的酒店，参数值为[['酒店各处提供wifi', '所有房间提供wifi', '部分房间提供wifi', '公共区域和部分房间提供wifi', '公共区域提供wifi']]
    """
    # print('function is calling')
    # print('htype:', htype)
    # print('rating_low:', rating_low)
    # print('rating_hi:', rating_hi)
    # print('price_low:', price_low)
    # print('price_hi:', price_hi)
    # print('subway:', subway)
    # print('facilities', facilities)

    engine = create_engine("sqlite:///hotel.db", echo=False)
    if htype not in hotel_types:
        htype = None
    if facilities and type(facilities) is List:
        facilities = [item for item in facilities if item in fac_types]
    if subway not in subway_names:
        subway = None

    hotel_ids = None
    if facilities:
        for fac in facilities:
            if type(fac) is str:
                with Session(engine) as session:
                    stmt = (
                        select(hotel_fac_table.c.hotel_id)
                        .where(
                            hotel_fac_table.c.fac_id == FacType.id, FacType.name == fac
                        )
                        .distinct()
                    )
                    hotel_id = [item for item in session.scalars(stmt)]
                if hotel_ids is None:
                    hotel_ids = set(hotel_id)
                else:
                    hotel_ids = hotel_ids & set(hotel_id)
            else:
                options = []
                for item in fac:
                    options.append(FacType.name == item)
                with Session(engine) as session:
                    stmt = (
                        select(hotel_fac_table.c.hotel_id)
                        .where(hotel_fac_table.c.fac_id == FacType.id)
                        .where(or_(*options))
                        .distinct()
                    )
                    hotel_id = [item for item in session.scalars(stmt)]
                if hotel_ids is None:
                    hotel_ids = set(hotel_id)
                else:
                    hotel_ids = hotel_ids & set(hotel_id)

    filters = []
    if hotel_ids:
        filters.append(Hotel.id.in_(hotel_ids))
    if htype:
        filters.extend((Hotel.type_id == HotelType.id, HotelType.name == htype))
    if rating_low:
        filters.append(Hotel.rating >= rating_low)
    if rating_hi:
        filters.append(Hotel.rating <= rating_hi)
    if price_low:
        filters.append(Hotel.price >= price_low)
    if price_hi:
        filters.append(Hotel.price <= price_hi)
    if subway:
        filters.append(Hotel.subway == subway)

    with Session(engine) as session:
        stmt = (
            select(Hotel)
            .join_from(Hotel, hotel_fac_table)
            .where(*filters)
            .distinct()
            .order_by(Hotel.rating)
            .limit(5)
        )
        return [item.to_json() for item in session.scalars(stmt)]


store = {}


def get_session_history(session_id: str) -> BaseChatMessageHistory:
    if session_id not in store:
        store[session_id] = InMemoryChatMessageHistory()
    return store[session_id]


def chat(sid):
    tools = [find_hotel]
    tool_map = {tool.name: tool for tool in tools}
    model = ChatOpenAI(model="gpt-4o", temperature=0)
    # model = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
    config = {"configurable": {"session_id": sid}}
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                system_prompt,
            ),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )
    chain = prompt | model.bind_tools(tools)
    with_message_history = RunnableWithMessageHistory(
        chain,
        get_session_history,
        input_messages_key="messages",
    )
    print('input "quit" to quit')
    user_input = input("user>: ")
    resp = with_message_history.invoke(
        {"messages": [HumanMessage(content=user_input)]},
        config=config,
    )

    while True:
        if resp.content:
            print("AI: ", resp.content)
            if user_input == "quit":
                break
            user_input = input("user>: ")
            resp = with_message_history.invoke(
                {"messages": [HumanMessage(content=user_input)]},
                config=config,
            )
        else:
            if not resp.tool_calls:
                break
            for func_item in resp.tool_calls:
                func_name = func_item["name"].lower()
                func = tool_map[func_name]
                output = func.invoke(func_item["args"])
                resp = with_message_history.invoke(
                    {
                        "messages": [
                            ToolMessage(
                                content=str(output), tool_call_id=func_item["id"]
                            )
                        ]
                    },
                    config=config,
                )
                break
                # print('resp final:', resp.content)


if __name__ == "__main__":
    chat("test")

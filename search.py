import dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
# from sqlalchemy import or_
from langchain_core.tools import tool
# from langchain_openai import ChatOpenAI
from consts import fac_types, hotel_types, subway_names, system_prompt
from data import Hotel
from langchain_core.output_parsers import StrOutputParser
from langchain.output_parsers import JsonOutputToolsParser
from langchain_openai import ChatOpenAI
from typing import Optional
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.chat_history import (
    BaseChatMessageHistory,
    InMemoryChatMessageHistory,
)
from langchain_core.runnables import (
    Runnable,
    RunnableLambda,
    RunnableMap,
    RunnablePassthrough,
)
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.messages import HumanMessage
from typing import Union
from operator import itemgetter
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder



dotenv.load_dotenv('env.conf')
# llm = ChatOpenAI(model="gpt-4o")  # 默认是gpt-3.5-turbo
# response = llm.invoke("你是谁")
# print(response.content)

@tool
def find_hotel(htype:Optional[str], rating_low:Optional[float], rating_hi:Optional[float], price_low:Optional[float], price_hi:Optional[float], subway:Optional[str], facilities:Optional[str], **kwargs):
    """ 
    根据用户的要求在数据库中搜索符合要求的酒店
    htype是字符串，表示酒店的档次，取值范围是'高档型', '舒适型', '经济型', '豪华型'
    rating_low是浮点数，是酒店评分的最低值
    rating_hi是浮点数，是酒店评分的最高值
    price_low是浮点数，是酒店价格的最低值
    price_hi是浮点数，是酒店价格的最高值   
    subway是字符串，表示附近的地铁站，取值范围是北京地铁站名
    facilities是字符串数组，表示酒店设施，取值范围在'健身房', '暖气', '行李寄存', '无烟房', 'SPA', '公共区域和部分房间提供wifi', '部分房间提供wifi', '早餐服务免费', '商务中心', '酒店各处提供wifi', '所有房间提供wifi', '早餐服务', '温泉', '接站服务', '接机服务', '吹风机', '中式餐厅', '24小时热水', '宽带上网', '租车', '室外游泳池', '会议室', '接待外宾', '国际长途电话', '收费停车位', '桑拿', '公共区域提供wifi', '残疾人设施', '室内游泳池', '叫醒服务', '免费国内长途电话', '免费市内电话', '西式餐厅', '洗衣服务', '棋牌室', '酒吧', '看护小孩服务'
    """
    print('function is calling')
    for key, value in kwargs.items():
        print(key, value)
    if htype not in hotel_types:
        htype = None
    if facilities and type(facilities) is list:
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

    engine = create_engine("sqlite:///hotel.db", echo=False)
    with Session(engine) as session:
        
        if filters:
            res = session.query(Hotel).filter(filters).all()
        else:
            res = session.query(Hotel).all()
        for item in res:
            print(item.to_json())

@tool
def multiply(first_int: int, second_int: int) -> int:
    """两个整数相乘"""
    return first_int * second_int


store = {}


def get_session_history(session_id: str) -> BaseChatMessageHistory:
    if session_id not in store:
        store[session_id] = InMemoryChatMessageHistory()
    return store[session_id]

tools = [multiply, find_hotel]
model = ChatOpenAI(model="gpt-4o", temperature=0)
tool_map = {tool.name: tool for tool in tools}
# 名称到函数的映射
tool_map = {tool.name: tool for tool in tools}

def call_tool(tool_invocation: dict) -> Union[str, Runnable]:
    """根据模型选择的 tool 动态创建 LCEL"""
    tool = tool_map[tool_invocation["type"]]
    print(itemgetter("args"))
    return RunnablePassthrough.assign(
        output=itemgetter("args") | tool
    )

def route(response):
    print(response)
    if len(response["functions"]) > 0:
        return response["functions"]
    else:
        return response["text"]

if __name__ == '__main__':
    call_tool_list = RunnableLambda(call_tool).map()
    llm_with_tools = model.bind_tools(tools) | {
        "functions": JsonOutputToolsParser() | call_tool_list,
        "text": StrOutputParser()
    } | RunnableLambda(route)
    # result = llm_with_tools.invoke("100乘以100是多少")
    # result = llm_with_tools.invoke("介绍一个4.5有wifi的酒店")


    # result = llm_with_tools.invoke("1024的平方是多少")
    # print(result)

    # result = llm_with_tools.invoke("你好")
    # print(result)


    # # .map() 使 function 逐一作用与一组输入
    # call_tool_list = RunnableLambda(call_tool).map()
    # print(result)
    # with_message_history = RunnableWithMessageHistory(model, get_session_history)
    # config = {"configurable": {"session_id": "test"}}

    config = {"configurable": {"session_id": "test"}}
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                system_prompt,
            ),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )
    # llm_with_tools = model.bind_tools(tools) | {
    #     "functions": JsonOutputToolsParser(),
    #     "text": StrOutputParser()
    # } | RunnableLambda(route)
    chain = prompt | model.bind_tools(tools) | {
        "functions": JsonOutputToolsParser()  | call_tool_list,
        "text": StrOutputParser()
    # }
    }| RunnableLambda(route)
    config = {"configurable": {"session_id": "test"}}
    with_message_history = RunnableWithMessageHistory(
        chain,
        get_session_history,
        input_messages_key="messages",
    )
    # while True:
    #     msg = input("input:")
    #     if msg == 'quit':
    #         break
    #     resp = with_message_history.invoke(
    #         {"messages": [HumanMessage(content=msg)]},
    #         config=config,
    #     )
    #     print(resp)

    msgs = [
        '评分大于4的酒店',
        '有wifi的酒店'
    ]
    for msg in msgs:
        resp = with_message_history.invoke(
            {"messages": [HumanMessage(content=msg)]},
            config=config,
        )
        print(resp)
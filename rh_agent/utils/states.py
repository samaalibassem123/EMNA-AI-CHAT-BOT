from typing import TypedDict, List, Annotated, Optional

from langchain_core.messages import BaseMessage
from langgraph.graph import add_messages


class AgentState(TypedDict):
    db_context:str
    messages: Annotated[list[BaseMessage], add_messages]
    user_input:str

    intent: Optional[str] # intent to classify the user input if it's for chating or to take actions on the db

    # sql queries
    sql_query:Optional[str]
    sql_is_safe:bool
    query_result:str

    # errors
    error:Optional[str]
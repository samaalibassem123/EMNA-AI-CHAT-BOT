from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig

from langgraph.checkpoint.memory import MemorySaver
from langgraph.constants import START, END
from langgraph.graph import StateGraph
from sqlalchemy.orm import Session
from rh_agent.utils.nodes import chat_node, schema_inspector, query_generator, \
    intent_classification, execute_query, generate_response, handle_error, validate_query
from rh_agent.utils.routes import intent_route, valid_query_route, execution_route
from rh_agent.utils.states import  AgentState



def node_wrapper(fn):
    def wrapper(state, config:RunnableConfig):
        session = config["configurable"]["session"]
        if "session" in fn.__code__.co_varnames:
            return fn(state,session)
        return fn(state)
    return wrapper



builder = StateGraph(AgentState)

# nodes
builder.add_node("intent_class", node_wrapper(intent_classification))
builder.add_node("schema_inspector", node_wrapper(schema_inspector))
builder.add_node("query_generator", node_wrapper(query_generator))
builder.add_node("validate_query", node_wrapper(validate_query))
builder.add_node("execute_query", node_wrapper(execute_query))
builder.add_node("handle_error", node_wrapper(handle_error))
builder.add_node("generate_response", node_wrapper(generate_response))
builder.add_node("chat_node",node_wrapper(chat_node))

# graph
builder.set_entry_point("intent_class")

# classify the user input if it's for normal chating or to make actions on the DB
builder.add_conditional_edges("intent_class", intent_route)


builder.add_edge("schema_inspector", "query_generator")
builder.add_edge("query_generator", "validate_query")

# Validate query
builder.add_conditional_edges("validate_query", valid_query_route)

# If there was Erros on the execution
builder.add_conditional_edges("execute_query", execution_route)


# THE END OF GRAPH
builder.add_edge("handle_error", END)
builder.add_edge("generate_response", END)
builder.add_edge("chat_node",END)

# Memory
checkpointer = MemorySaver()

graph = builder.compile(checkpointer=checkpointer)


import json

LAST_NODES = ['chat_node', 'generate_response', 'handle_error']
NODE_LABELS = {
    "intent_class": "Understanding user request...",

    "chat_node": "Generating chat response...",

    "schema_inspector": "Reading database schema...",

    "query_generator": "Generating SQL query...",

    "validate_query": "Validating query safety...",

    "execute_query": "Executing database query...",

    "generate_response": "Writing analytical report..."
}
def generate_stream(message: str, thread_id: str, session: Session):
    config = RunnableConfig(
        configurable={
            "thread_id":thread_id,
            "session":session
        }
    )
    inputs = {
        "messages": [HumanMessage(content=message)],
        "user_input":message
    }

    try:
        is_last_node = False
        for event in graph.stream_events(inputs, config):
            event_type = event["event"]
            name = event.get("name", "")


            # STREAM Agents STEPS
            if event_type == "on_chain_start" and name in NODE_LABELS :
                yield json.dumps({
                    "type":"step",
                    "content":NODE_LABELS[name]
            }) + "\n"


            # STREAM AI response
            if name in LAST_NODES:
                is_last_node = True

            if event_type == "on_chat_model_stream" and is_last_node:
                token = event["data"]["chunk"].content

                if token:
                    yield json.dumps({
                        "type": "token",
                        "content": token
                    }) + "\n"

    except Exception as e:
        yield json.dumps({"type": "error", "content": str(e)}) + "\n"
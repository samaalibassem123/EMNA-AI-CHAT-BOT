import json
from typing import Any

from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import MemorySaver
from langgraph.constants import START, END
from langgraph.graph import StateGraph
from sqlalchemy.orm import Session

from rh_agent.utils.nodes import (
    chat_node,
    schema_inspector,
    query_generator,
    intent_classification,
    execute_query,
    generate_response,
    handle_error,
    validate_query,
)
from rh_agent.utils.routes import intent_route, valid_query_route, execution_route
from rh_agent.utils.states import AgentState


def node_wrapper(fn):
    def wrapper(state, config: RunnableConfig):
        session = config["configurable"]["session"]

        # If the node function expects a session, pass it.
        if "session" in fn.__code__.co_varnames:
            return fn(state, session)

        return fn(state)

    return wrapper


builder = StateGraph(AgentState)

# Nodes
builder.add_node("intent_class", node_wrapper(intent_classification))
builder.add_node("schema_inspector", node_wrapper(schema_inspector))
builder.add_node("query_generator", node_wrapper(query_generator))
builder.add_node("validate_query", node_wrapper(validate_query))
builder.add_node("execute_query", node_wrapper(execute_query))
builder.add_node("handle_error", node_wrapper(handle_error))
builder.add_node("generate_response", node_wrapper(generate_response))
builder.add_node("chat_node", node_wrapper(chat_node))

# Entry point
builder.set_entry_point("intent_class")

# Routes
builder.add_conditional_edges("intent_class", intent_route)
builder.add_edge("schema_inspector", "query_generator")
builder.add_edge("query_generator", "validate_query")
builder.add_conditional_edges("validate_query", valid_query_route)
builder.add_conditional_edges("execute_query", execution_route)

# End nodes
builder.add_edge("handle_error", END)
builder.add_edge("generate_response", END)
builder.add_edge("chat_node", END)

# Memory
checkpointer = MemorySaver()
graph = builder.compile(checkpointer=checkpointer)

LAST_NODES = {"chat_node", "generate_response", "handle_error"}

NODE_LABELS = {
    "intent_class": "Understanding user request...",
    "chat_node": "Generating chat response...",
    "schema_inspector": "Reading database schema...",
    "query_generator": "Generating SQL query...",
    "validate_query": "Validating query safety...",
    "execute_query": "Executing database query...",
    "generate_response": "Writing analytical report...",
}


def _extract_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        for key in ("content", "text", "output", "response"):
            if key in value and value[key]:
                return str(value[key])
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def generate_stream(message: str, thread_id: str, session: Session):
    config = RunnableConfig(
        configurable={
            "thread_id": thread_id,
            "session": session,
        }
    )

    inputs = {
        "messages": [HumanMessage(content=message)],
        "user_input": message,
    }

    try:
        # LangGraph sync streaming API
        for chunk in graph.stream(inputs, config, stream_mode="updates"):
            if not isinstance(chunk, dict):
                continue

            for node_name, node_output in chunk.items():
                # Show step text
                if node_name in NODE_LABELS:
                    yield json.dumps(
                        {
                            "type": "step",
                            "content": NODE_LABELS[node_name],
                        }
                    ) + "\n"

                # Final response nodes
                if node_name in LAST_NODES:
                    text = _extract_text(node_output)

                    if text:
                        yield json.dumps(
                            {
                                "type": "token",
                                "content": text,
                            }
                        ) + "\n"

    except Exception as e:
        yield json.dumps(
            {
                "type": "error",
                "content": str(e),
            }
        ) + "\n"
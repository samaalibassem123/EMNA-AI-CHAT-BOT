import json
import re

from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from sqlalchemy import text
from sqlalchemy.orm import Session

from rh_agent.utils.agent import rh_agent
from rh_agent.utils.contexts import get_table_context, get_last_user_message
from rh_agent.utils.states import AgentState


def intent_classification(state: AgentState):
    try:
        user_input = state["user_input"]
        prompt = f"""
        You are an intent classification system for an assistant.

        Your job is to classify the user input into ONLY ONE label:

        - "chat": greetings, explanations, opinions, general questions, or conversations that do NOT require database access.
        - "database": any request that involves retrieving, filtering, listing, updating, or querying structured data (e.g. employees, users, orders, reports).

        IMPORTANT RULES:
        - If the user asks to "show", "list", "get", "find", "display", or "retrieve" data → classify as "database"
        - If the request mentions business entities like employees, customers, orders, sales, KPIs → likely "database"
        - If the request is conceptual or conversational → "chat"

        OUTPUT RULE:
        Return ONLY one word: chat or database. No explanation.

        EXAMPLES:

        Input: Hello, how are you?
        Output: chat

        Input: Explain what a KPI is
        Output: chat

        Input: Show me all employees
        Output: database

        Input: Get users who signed up last week
        Output: database

        Input: Can you help me understand SQL joins?
        Output: chat

        Now classify:

        Input: {user_input}
        Output:
        """


        SystemPrompt = {
            "messages":[SystemMessage(content=prompt),HumanMessage(user_input)]
        }
        response = rh_agent.invoke(SystemPrompt)

        intent = response["messages"][-1].content.strip().lower()

        if intent not in ("chat", "database"):
            intent = "chat"

        print("intent:", intent)

        return {"intent": intent}
    except Exception as e:
        print("intent error",e)
        return {"error":e, "intent":"chat"}

def schema_inspector(state:AgentState, session:Session):
    context = get_table_context(session,["employees","departments","employee_attendance_event","attendance_events","attendance"])
    print(context)
    return {
        "db_context":context
    }

def query_generator(state:AgentState):
    try:
        last_message = get_last_user_message(state.get("messages", []))
        if not last_message:
            return {
                "error":"Message doest not exist"
            }
        prompt = f"""
You are a Microsoft SQL Server (T-SQL) expert specialized in Data Warehousing.

Write ONE efficient SQL Server query.

Rules:
- Use proper T-SQL syntax (SQL Server compatible)
- Use WHERE filters early to reduce scanned data (especially on fact tables)
- Always use TOP instead of LIMIT
- Always schema-qualify tables (e.g., dbo.FactSales, dbo.DimDate)
- NEVER use SELECT * — explicitly select only required columns
- Use clear and meaningful aliases for tables and columns
- Use AS to name ALL output columns
- Use CTEs (WITH clause) for complex transformations
- Use appropriate JOINs between fact and dimension tables (star/galaxy schema)
- Prefer INNER JOIN unless missing data is expected (then use LEFT JOIN)
- Aggregate only when necessary and always use GROUP BY correctly
- When filtering by date, use indexed date keys or date columns efficiently
- Avoid unnecessary subqueries — prefer CTEs or joins
- Ensure query is optimized for large datasets (5000+ rows, typically much larger in DW)

Schema:
{state["db_context"]}

Question:
{state["user_input"]}

Output:
Return ONLY the SQL Server query. No explanations, no comments.
"""
        SystemPrompt = {
            "messages":[SystemMessage(content=prompt), HumanMessage(state['user_input'])]
        }
        query = rh_agent.invoke(SystemPrompt)["messages"][-1].content

        cleaned_query = query.strip().strip("```sql").strip("```").strip()

        print("query:" ,cleaned_query)
        return {
            "sql_query":cleaned_query
        }
    except Exception as e:
        print(e)
        return {"error":str(e)}


async def validate_query(state:AgentState):
    sql = state['sql_query'].strip().upper()

    forbidden = ["INSERT", "UPDATE", "DELETE", "DROP", "TRUNCATE", "ALTER", "CREATE", "GRANT"]

    is_select = sql.startswith("SELECT") or sql.startswith("WITH")

    has_forbidden = any(re.search(rf"\b{k}\b", sql) for k in forbidden)

    is_safe = is_select and not has_forbidden

    print("query is safe:", is_safe)

    return {
        "error": None if is_safe else f"Blocked unsafe SQL: {sql[:120]}",
        "sql_is_safe":is_safe
    }



def execute_query(state:AgentState, session:Session):
    try:
        query = state["sql_query"]

        result = session.execute(text(query))
        res = result.mappings().all()
        print("res" , res)
        query_result = json.dumps(res, indent=2, default=str)
        print("query result : " , query_result)
        return {
            "query_result":query_result
        }
    except Exception as e:
        print(e)
        return {
            "error":e,
            "query_result":"found nothing"
        }


def handle_error(state:AgentState):
    error = state["error"]
    query_is_safe = state["sql_is_safe"]
    print("error",error)
    prompt =  f'''
        Always check the safety of the user input and the generate query, Write a professional Error message
        example : this action is forbidden
        context : {error}
        user_input:{state['user_input']}
        Query safety : {query_is_safe}
    '''
    SystemPrompt = {
        "messages": [
            SystemMessage(content=prompt),
            HumanMessage(state['user_input'])
        ]
    }
    response = rh_agent.invoke(SystemPrompt)

    return {
        "messages":state["messages"] + [response["messages"][-1]]
    }


def generate_response(state:AgentState):

    prompt = f"""
        You are a senior data analyst. Write a professional Markdown report.
        
        Include:
        1. Executive summary (2-3 sentences)
        2. Key findings (bullet points)
        3. Data table of the most important rows
        4. Show SQL used
        4. Recommendations or next steps
        
        Original question: {state["user_input"]}
        
        SQL used:
        ```sql
        {state['sql_query']}
        ```
        Data Summary or result:
        {state['query_result']}
     
        """
    SystemPrompt = {
        "messages":[
            SystemMessage(content=prompt),
            HumanMessage(state['user_input'])
        ]
    }
    llm_response = rh_agent.invoke(SystemPrompt)

    return {
        "messages":state["messages"] + [llm_response["messages"][-1]]
    }

def chat_node(state: AgentState):
    result = rh_agent.invoke({
        "messages": state["messages"]
    })

    return {
        "messages":state["messages"]+ [result["messages"][-1]]
    }



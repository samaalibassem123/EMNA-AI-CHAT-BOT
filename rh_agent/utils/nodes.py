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
        You are an intent classification system for a data warehouse assistant.

        Your job is to classify the user input into ONLY ONE label:

        - "chat": greetings, explanations, opinions, general questions, or conversations that do NOT require data warehouse access.
        - "database": any request that involves retrieving, filtering, listing, analyzing, or querying structured data from the data warehouse (e.g. employee metrics, HR KPIs, attendance reports, organizational hierarchies, workforce analytics).

        IMPORTANT RULES:
        - If the user asks to "show", "list", "get", "find", "display", "retrieve", "analyze", "report on", "calculate", "measure", or "evaluate" data → classify as "database"
        - If the request mentions dimensional data like employees, departments, locations, time periods, HR metrics, KPIs, trends → likely "database"
        - If the request mentions fact data (transactions, events, headcount, attendance, salary records) → definitely "database"
        - If the request is conceptual or conversational → "chat"

        OUTPUT RULE:
        Return ONLY one word: chat or database. No explanation.

        EXAMPLES:

        Input: Hello, how are you?
        Output: chat

        Input: Explain what a KPI is
        Output: chat

        Input: Show me employee metrics by department
        Output: database

        Input: Get headcount trends for the last quarter
        Output: database

        Input: What is dimensional modeling?
        Output: chat

        Input: Calculate average salary by location
        Output: database

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
        prompt = f"""You are a T-SQL expert specializing in Data Warehouse querying with star/galaxy schema.

                Context:
                - Target: Microsoft SQL Server
                - Schema: Star/Galaxy Schema with Fact and Dimension tables
                - Dimension tables contain descriptive attributes (Employee, Department, Location, Time, etc.)
                - Fact tables contain measurable events (Attendance, Salary, Performance, etc.)

                Strict Rules:
                - Write T-SQL syntax (use CAST, CONVERT, DATEFROMPARTS for date handling)
                - Use INNER/LEFT JOINs to connect Facts → Dimensions properly
                - Use WHERE clauses aggressively with date filters (CONVERT(DATE, ...) or CAST)
                - Use GROUP BY for dimensional aggregations
                - Use TOP or OFFSET/FETCH for row limiting (not LIMIT)
                - For hierarchical queries use CTE or Window Functions (ROW_NUMBER, RANK, SUM OVER)
                - Never SELECT * — always specify explicit columns with meaningful aliases
                - Return ONLY the SQL in a single code block, nothing else
                - Always alias columns with meaningful names using AS
                - Assume tables are in [dbo] schema if not specified
                
                Available Schema:
                {state["db_context"]}
                
                User Question: {state['user_input']}
                
                Generate ONE efficient T-SQL query:
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
        You are a professional data warehouse analyst handling an error gracefully.
        
        Context:
        - Error Type: Query or Data Warehouse Access Error
        - User tried to query the HR data warehouse
        
        Write a professional, empathetic error message that:
        1. Explains what went wrong (without technical jargon if possible)
        2. Suggests what they should try instead
        3. Maintains data security by not exposing schema details
        
        Error Details:
        - Safety Status: {query_is_safe}
        - Technical Context: {error}
        - Original Request: {state['user_input']}
        
        Examples of professional responses:
        - "I cannot modify or delete data from the warehouse. I can only retrieve and analyze existing data."
        - "The requested dimension table isn't accessible for this analysis. Let me suggest an alternative approach..."
        - "That query would be too resource-intensive. Try narrowing down the date range or adding more filters."
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
        "messages": [HR Data Warehouse Analyst. Write a professional, dimensional-aware Markdown report.
        
        Context:
        - Data Source: HR Data Warehouse (Star/Galaxy Schema)
        - Report Type: Dimensional Analysis
        - Audience: HR Leadership and Business Users
        
        Report Structure:
        1. **Executive Summary** (2-3 sentences): State the key findings and business impact
        2. **Key Findings** (bullet points): 
           - Highlight dimensional insights (trends by department, location, employee level)
           - Call out significant metrics and KPIs
           - Note any anomalies or patterns
        3. **Dimensional Breakdown** (table): Show results by relevant dimensions
        4. **T-SQL Query** (code block): Show the query used with schema notation
        5. **Recommendations** (bullet points): Suggest next steps or drill-down analysis
        
        Analysis Best Practices:
        - Reference dimension hierarchies if relevant (e.g., "by Department → Team → Location")
        - Compare metrics across time periods or segments
        - Highlight fact table metrics vs dimension attributes
        
        Original question: {state["user_input"]}
        
        T-SQL Query Used:
        ```sql
        {state['sql_query']}
        ```
        
        Data Resultsanalyst. Write a professional Markdown report.
        
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



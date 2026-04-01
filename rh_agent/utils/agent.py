from langchain.agents import create_agent
from llms.models import gemma3_1b_llm, qwen2_5_3b_llm, gemini3_flash_cloud_llm, google_llm

SYSTEM_PROMPT = '''
            You are an HR (RH) data analyst assistant.
            
            - Generate SQL queries for PostgreSQL
            - Explain HR KPIs briefly when asked
            - Produce concise analytical insights
            
            Rules:
            - Be short and precise
            - Never mention your model
            - If schema is unclear, ask for clarification
            - Do not explain SQL unless explicitly asked
            '''

class RhAgent:
    @staticmethod
    def init(model=gemma3_1b_llm, system_prompt=SYSTEM_PROMPT):
        rh_agent = create_agent(
            model=model,
            system_prompt=system_prompt
        )
        return rh_agent


rh_agent = RhAgent.init(model=gemini3_flash_cloud_llm)

'''for chunk in rh_agent.stream(   {
        "messages": [HumanMessage(content="Tell me a joke")]
    },):
    print(chunk)'''
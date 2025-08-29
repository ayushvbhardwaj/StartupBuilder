# cto_service.py

import os
import redis
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI

# Import our sandbox tool
from tools import run_code_in_sandbox

# --- Setup ---
load_dotenv()
print("## CTO Service: Defining LLM connection...")
llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    temperature=0.7,
    google_api_key=os.getenv("GEMINI_API_KEY")
)

# --- CTO Prompt Definitions ---
print("## CTO Service: Defining Agent Prompts...")

# Prompt 1: For creating the high-level technical plan
cto_planning_prompt = ChatPromptTemplate.from_messages([
    ("system",
     "You are a seasoned and decisive CTO. Your goal is to translate a business plan into a "
     "detailed and actionable technical specification. You must make definitive choices "
     "for the technology stack. Do not offer alternatives or options. Your word is final."),
    ("human",
     "Here is the business plan from the CEO:\n\n{business_plan}\n\n"
     "Based on this plan, create a complete technical specification...")
])

# Prompt 2: For extracting the first coding task from the plan
cto_task_extraction_prompt = ChatPromptTemplate.from_messages([
    ("system",
     "You are a project manager. Your goal is to extract the very first, simplest coding task "
     "from a technical plan. This task should be the absolute first step in building the MVP, "
     "like setting up a basic 'Hello World' server."),
    ("human",
     "Here is the technical plan:\n\n{technical_plan}\n\n"
     "Based on this, what is the single, specific coding task for the developer to start with? "
     "Describe it in one sentence.")
])


# --- Redis Connection ---
print("## CTO Service: Connecting to Redis...")
redis_client = redis.Redis(host='localhost', port=6379, db=0)
pubsub = redis_client.pubsub()
pubsub.subscribe('ceo_plan')

# --- Main Execution Logic ---
def run_cto_service():
    print("## CTO Service: Listening for business plans on channel 'ceo_plan'...")
    output_parser = StrOutputParser()
    
    # Create two separate chains for the CTO's two distinct thought processes
    cto_planning_chain = cto_planning_prompt | llm | output_parser
    cto_task_extraction_chain = cto_task_extraction_prompt | llm | output_parser

    for message in pubsub.listen():
        if message['type'] == 'message':
            business_plan = message['data'].decode('utf-8')
            print("\n## CTO Service: Received a new business plan!")
            
            # --- Step 1: Create the Technical Plan ---
            print("## CTO is creating the technical plan...")
            technical_plan = cto_planning_chain.invoke({"business_plan": business_plan})
            print("\n\n########################")
            print("## Final Technical Plan from the CTO:")
            print(technical_plan)
            print("########################\n")

            # --- Step 2: Autonomously Decide on the First Task ---
            print("## CTO is deciding on the first coding task...")
            coding_task = cto_task_extraction_chain.invoke({"technical_plan": technical_plan})
            print(f"## CTO has defined the first task as: '{coding_task}'")

            # --- Step 3: Trigger the Sandbox with the Autonomous Task ---
            print("## CTO Service: Triggering developer agent in sandbox...")
            final_code = run_code_in_sandbox(coding_task)

            print("\n\n########################")
            print("## Final Code from the Developer Agent:")
            print(final_code)
            print("########################\n")

            print("\n## CTO Service: Full cycle complete. Listening for next plan...")

if __name__ == "__main__":
    run_cto_service()

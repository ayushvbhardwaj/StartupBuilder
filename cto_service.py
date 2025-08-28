# cto_service.py

import os
import redis
import json
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI

# --- Setup ---
load_dotenv()
print("## CTO Service: Defining LLM connection...")
llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    temperature=0.7,
    google_api_key=os.getenv("GEMINI_API_KEY")
)

# --- CTO Prompt Definition ---
print("## CTO Service: Defining Agent Prompt...")
# In cto_service.py

cto_prompt = ChatPromptTemplate.from_messages([
    ("system",
     "You are a seasoned CTO. Your goal is to translate a business plan into a "
     "detailed and **actionable** technical specification. **You must make definitive choices** "
     "for the technology stack. **Do not offer alternatives or options.** Your word is final."),
    ("human",
     "Here is the business plan created by the CEO:\n\n{business_plan}\n\n"
     "Based on this plan, create a complete technical specification. "
     "This must include **your final choice** for the recommended tech stack (languages, frameworks, database), "
     "a high-level system architecture description, API endpoint definitions, "
     "and a sprint-by-sprint development roadmap. Your final output should be a comprehensive markdown document.")
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
    cto_chain = cto_prompt | llm | output_parser

    for message in pubsub.listen():
        if message['type'] == 'message':
            business_plan = message['data'].decode('utf-8')
            print("\n## CTO Service: Received a new business plan!")
            print("## CTO is working...")

            technical_plan = cto_chain.invoke({"business_plan": business_plan})

            print("\n\n########################")
            print("## Final Technical Plan from the CTO:")
            print(technical_plan)
            print("\n## CTO Service: Task complete. Listening for next plan...")

if __name__ == "__main__":
    run_cto_service()

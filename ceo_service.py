# ceo_service.py

import os
import redis
import json
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI

# --- Setup ---
load_dotenv()
print("## CEO Service: Defining LLM connection...")
llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    temperature=0.7,
    google_api_key=os.getenv("GEMINI_API_KEY")
)

# --- CEO Prompt Definition ---
print("## CEO Service: Defining Agent Prompt...")
# Prompt for the CEO Agent
ceo_prompt = ChatPromptTemplate.from_messages([
    ("system",
     "You are a visionary CEO. Your goal is to develop a comprehensive, "
     "validated business plan for a new software product. You are data-driven and decisive."),
    ("human",
     "Create a detailed business plan for the following idea: {idea}. "
     "The plan must include market analysis, target audience, monetization strategy, "
     "and a list of 3-5 key features. Your final output should be a well-structured markdown document.")
])


# --- Redis Connection ---
print("## CEO Service: Connecting to Redis...")
redis_client = redis.Redis(host='localhost', port=6379, db=0)

# --- Main Execution Logic ---
if __name__ == "__main__":
    print("## CEO Service: Starting Manual Orchestration...")
    output_parser = StrOutputParser()
    ceo_chain = ceo_prompt | llm | output_parser

    print("## CEO is working...")
    initial_idea = "An AI-powered app for personalized gardening schedules."
    business_plan = ceo_chain.invoke({"idea": initial_idea})

    print("\n--- CEO's Business Plan ---")
    print(business_plan)

    # --- Publish to Redis ---
    print("\n## CEO Service: Publishing business plan to Redis channel 'ceo_plan'...")
    redis_client.publish('ceo_plan', business_plan)
    print("## CEO Service: Plan published. Shutting down.")

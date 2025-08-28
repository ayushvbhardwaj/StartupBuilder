# main.py

import os
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

# Import the core libraries for interacting with the Gemini API
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI

# --- Step 1: Define Your LLM Connection ---
# This is our direct connection to the Gemini Flash model.
print("## Defining LLM connection...")
llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    temperature=0.7,
    google_api_key=os.getenv("GEMINI_API_KEY")
)

# --- Step 2: Define the Agent Prompts ---
# Instead of "Agents," we define prompts. Each prompt is a template
# that structures the input we send to the LLM.

print("## Defining Agent Prompts...")

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

# Prompt for the CTO Agent
cto_prompt = ChatPromptTemplate.from_messages([
    ("system",
     "You are a seasoned CTO. Your goal is to translate a business plan into a "
     "detailed technical specification and development roadmap."),
    ("human",
     "Here is the business plan created by the CEO:\n\n{business_plan}\n\n"
     "Based on this plan, create a complete technical specification. "
     "This must include the recommended tech stack (languages, frameworks, database), "
     "a high-level system architecture description, API endpoint definitions, "
     "and a sprint-by-sprint development roadmap. Your final output should be a comprehensive markdown document.")
])

# --- Step 3: Manually Orchestrate the Workflow ---
# This is where we replace the CrewAI framework with our own logic.

print("## Starting Manual Orchestration...")

# 1. Define the "chains" for each agent. A chain combines the prompt, the LLM,
#    and an output parser to create a reusable execution flow.
output_parser = StrOutputParser()
ceo_chain = ceo_prompt | llm | output_parser
cto_chain = cto_prompt | llm | output_parser

# 2. Run the CEO chain to get the business plan.
print("## CEO is working...")
initial_idea = "An AI-powered app for personalized gardening schedules."
business_plan = ceo_chain.invoke({"idea": initial_idea})

print("\n--- CEO's Business Plan ---")
print(business_plan)

# 3. Run the CTO chain, feeding it the CEO's output.
print("\n## CTO is working...")
technical_plan = cto_chain.invoke({"business_plan": business_plan})

# --- Step 4: Print the Final Result ---
print("\n\n########################")
print("## Final Technical Plan from the CTO:")
print(technical_plan)

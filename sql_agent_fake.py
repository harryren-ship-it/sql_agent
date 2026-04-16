import os
from langchain_community.agent_toolkits.sql.base import create_sql_agent
from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
from langchain_community.utilities.sql_database import SQLDatabase
from sqlalchemy import create_engine
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI


# === Step 0: Set up Google API key ===
load_dotenv()
os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")  # 确保在 .env 文件中设置了 GOOGLE_API_KEY=your_api_key_here

# === Step 1: Set up LLM ===
llm = ChatGoogleGenerativeAI(
    model="models/gemini-2.0-flash",  # could be changed to gemini-1.5-pro or other models
    temperature=0.2
)

# === Step 2: Connect to the database ===
# db_uri = "sqlite:///university.sqbpro"
# engine = create_engine(db_uri)
# db = SQLDatabase(engine)

db = SQLDatabase.from_uri("sqlite:///university.db")

# === Step 3: Build LLM + Agent toolkit ===
toolkit = SQLDatabaseToolkit(db=db, llm=llm)

agent_executor = create_sql_agent(
    llm=llm,
    toolkit=toolkit,
    verbose=True
)


agent_executor.invoke("List all tables in the database.")



# === Step 4: Run queries ===
while True:
    user_input = input("\nEnter a natural language query (or type 'quit' to exit):\n> ")
    if user_input.strip().lower() == "quit":
        break
    try:
        response = agent_executor.invoke(user_input)
        print(f"\n🧠 AI Agent Response:\n{response}")
    except Exception as e:
        print(f"❌ Error: {e}")

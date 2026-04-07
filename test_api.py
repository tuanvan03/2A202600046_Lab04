import os 
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

llm = ChatOpenAI(model='gpt-4o-mini', max_tokens=20)
response = llm.invoke("Hello, how are you? My name is Tuan")
print(response)
print(response.content)
import collections
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from tools import search_flights, search_hotels, calculate_budget
from dotenv import load_dotenv
import os
import json
from datetime import datetime

load_dotenv()

# 1. Read System prompt 
"""
Read instruction in system_prompt.txt
"""
with open("system_prompt.txt", "r", encoding="utf-8") as f:
    SYSTEM_PROMPT = f.read()

# 2. Define State
"""
Define state of the agent. This is central state of the graph.
messages contain all messages in the conversation such as: user message, agent response, tool call, tool response.
Using Annotated and add_messages to automatically append messages to the state. Agent always have full context of the conversation.
=> Memory of the agent
"""
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]

# 3. Initialize LLM and tools
"""
Assign tools to LLM.
With bind_tools, LLM will automatically call tools when needed.
Langgraph don't handle tool calling, it just route to tool node if LLM call tool. It's quite same ReAct pattern.
"""
tools_list = [search_flights, search_hotels, calculate_budget]
llm = ChatOpenAI(model="gpt-4o-mini")
llm_with_tools = llm.bind_tools(tools_list)

# 4. Define Agent Node
"""
This node is the core of the agent. It takes the current state and returns the next state.
"""
def agent_node(state: AgentState):
    messages = state["messages"]

    # Add system prompt to the first message if not already present
    # Make sure system prompt is always the first message
    if not isinstance(messages[0], SystemMessage):
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages
    response = llm_with_tools.invoke(messages)

    # In this step, LLM can return 2 types of response:
    # 1. Direct response: LLM directly answer the user's question
    # 2. Tool call: LLM call tools to get more information
    # If LLM call tool, we need to call the tool and return the result to LLM
    # If LLM directly answer, we just return the response
    if response.tool_calls:
        for tc in response.tool_calls:
            print(f"Call tool: {tc['name']} with args: {tc['args']}")
    else:
        print(f"Response directly")

    # Return the current state with new response, it will be added to messages
    return {"messages": [response]}

# 5. Build graph
builder = StateGraph(AgentState)

# Add nodes
builder.add_node("agent", agent_node)
builder.add_node("tools", ToolNode(tools_list))

# Add edges
builder.add_edge(START, "agent")
builder.add_conditional_edges(
    "agent",
    tools_condition,
    ["tools", END]
)

builder.add_edge("tools", "agent")

# Using memory to save chat history
memory = MemorySaver()
graph = builder.compile(checkpointer=memory)

# 6. Chat loop
if __name__ == "__main__":
    # Ensure logs directory always exists
    if not os.path.exists("logs"):
        os.makedirs("logs")
    
    # Create log file with timestamp
    log_file = f"logs/chat_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    print(f"TravelBuddy Agent started. Type 'exit' to quit.")
    print(f"(Chat history is automatically saved at: {log_file})")
    
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"=== START CHAT SESSION ({datetime.now().strftime('%d/%m/%Y %H:%M:%S')}) ===\n")

    # Config session for one id
    config = {"configurable": {"thread_id": "session_1"}}

    while True:
        try:
            user_input = input("You: ")
            if user_input.lower() == "exit":
                break
            
            response = graph.invoke({"messages": [HumanMessage(content=user_input)]}, config=config) # config is used to save chat history
            agent_response = response['messages'][-1].content
            
            print(f"TravelBuddy: {agent_response}")
            
            # Record events to the log file
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(f"You: {user_input}\n")
                
                # Log if the agent called any tools during this turn
                for msg in response["messages"]:
                    if getattr(msg, "tool_calls", None):
                        tools_called = [{"name": t["name"], "args": t["args"]} for t in msg.tool_calls]
                        f.write(f" -> [Tool Called]: {json.dumps(tools_called, ensure_ascii=False)}\n")
                
                f.write(f"TravelBuddy: {agent_response}\n")
                f.write("-" * 50 + "\n")
                
        except KeyboardInterrupt:
            print("\nExiting program. Goodbye!")
            with open(log_file, "a", encoding="utf-8") as f:
                f.write("=== END CHAT SESSION VIA KEYBOARD INTERRUPT ===\n")
            break
        except Exception as e:
            print(f"\n[Error] Execution encountered an issue (API error or Tool fail): {e}")
            print("TravelBuddy: Sorry, the system is currently unable to respond due to a technical issue. Please try again later.")
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(f"\n[SYSTEM ERROR]: {str(e)}\n\n")
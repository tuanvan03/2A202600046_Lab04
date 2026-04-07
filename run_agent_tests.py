import os
import json
from datetime import datetime
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage
from agent import graph

def setup_logger():
    if not os.path.exists("logs"):
        os.makedirs("logs")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = f"logs/test_run_{timestamp}.log"
    return log_file

def format_message(msg):
    if isinstance(msg, HumanMessage):
        return f"User: {msg.content}"
    elif isinstance(msg, AIMessage):
        output = f"Agent: {msg.content if msg.content else '[No Output]'}"
        if hasattr(msg, "tool_calls") and msg.tool_calls:
            output += f"\n  [Tools Gọi]: {json.dumps(msg.tool_calls, indent=2, ensure_ascii=False)}"
        return output
    elif isinstance(msg, ToolMessage):
        return f"Tool [{msg.name}]: Dữ liệu trả về:\n  {msg.content}"
    elif isinstance(msg, SystemMessage):
        return f"System: {msg.content[:100]}..."
    else:
        return f"Unknown message type: {type(msg)}"

def run_test_case(test_number, name, user_input, expectation, log_file):
    print(f"\n{'='*50}")
    print(f"Chạy Test {test_number}: {name}")
    print(f"User Input: '{user_input}'")
    print(f"Kỳ vọng: {expectation}")
    print(f"{'-'*50}")
    
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"\n\n{'='*50}\n")
        f.write(f"TEST {test_number}: {name}\n")
        f.write(f"USER INPUT: {user_input}\n")
        f.write(f"EXPECTATION: {expectation}\n")
        f.write(f"{'-'*50}\n")
        
        # Invoke agent
        f.write("STARTING AGENT EXECUTION...\n")
        try:
            response = graph.invoke({"messages": [HumanMessage(content=user_input)]})
            
            # Log all messages
            for i, msg in enumerate(response["messages"]):
                formatted = format_message(msg)
                f.write(f"\nStep {i+1}: {formatted}\n")
                
                if isinstance(msg, AIMessage) and getattr(msg, "tool_calls", None):
                    print(f" -> [Agent gọi tool]: {[t['name'] for t in msg.tool_calls]}")
            
            final_response = response["messages"][-1].content
            print(f"\n[Kết quả cuối cùng]:\n{final_response}")
            
            f.write("\nEXECUTION COMPLETED.\n")
            
        except Exception as e:
            error_msg = f"LỖI KHI CHẠY TEST: {str(e)}"
            print(error_msg)
            f.write(f"\n{error_msg}\n")

if __name__ == "__main__":
    log_file = setup_logger()
    print(f"Đã tạo file log tại folder 'logs'. File log hiện tại: {log_file}")
    
    tests = [
        {
            "name": "Direct Answer (Không cần tool)",
            "input": "Xin chào! Tôi đang muốn đi du lịch nhưng chưa biết đi đâu.",
            "expectation": "Agent chào hỏi, hỏi thêm về sở thích/ngân sách/thời gian. Không gọi tool nào."
        },
        {
            "name": "Single Tool Call",
            "input": "Tìm giúp tôi chuyến bay từ Hà Nội đi Đà Nẵng",
            "expectation": "Gọi search_flights('Hà Nội', 'Đà Nẵng'), liệt kê 4 chuyến bay."
        },
        {
            "name": "Multi-Step Tool Chaining",
            "input": "Tôi ở Hà Nội, muốn đi Phú Quốc 2 đêm, budget 5 triệu. Tư vấn giúp!",
            "expectation": "Agent phải tự chuỗi nhiều bước: search_flights -> search_hotels -> calculate_budget, tổng hợp thành gợi ý hoàn chỉnh."
        },
        {
            "name": "Missing Info / Clarification",
            "input": "Tôi muốn đặt khách sạn",
            "expectation": "Agent hỏi lại: thành phố nào? bao nhiêu đêm? ngân sách bao nhiêu? Không gọi tool vội."
        },
        {
            "name": "Guardrail / Refusal",
            "input": "Giải giúp tôi bài tập lập trình Python về linked list",
            "expectation": "Từ chối lịch sự, nói rằng chỉ hỗ trợ về du lịch."
        }
    ]
    
    for i, t in enumerate(tests, 1):
        run_test_case(i, t["name"], t["input"], t["expectation"], log_file)
        
    print(f"\nĐã chạy xong 5 test cases. Log chi tiết được lưu trong: {log_file}")

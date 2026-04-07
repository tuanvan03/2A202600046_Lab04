from data_mock import FLIGHTS_DB, HOTELS_DB
from langchain_core.tools import tool

def format_currency(amount: int) -> str:
    return f"{amount:,}".replace(",", ".") + "đ"

@tool
def search_flights(origin: str, destination: str) -> str:
    """
    Tìm kiếm các chuyến bay giữa hai thành phố.
    Tham số:
    - origin: thành phố khởi hành (VD: 'Hà Nội', 'Hồ Chí Minh')
    - destination: thành phố đến (VD: 'Đà Nẵng', 'Phú Quốc')
    Trả về danh sách chuyến bay với hãng, giờ bay, giá vé.
    Nếu không tìm thấy chuyến bay, trả về thông báo không có chuyến.
    """
    # TODO: Sinh viên tự triển khai
    # - Tra cứu FLIGHTS_DB với key (origin, destination)
    # - Nếu tìm thấy -> format danh sách chuyến bay dễ đọc, bao gồm giá tiền
    # - Nếu không tìm thấy -> thử tra ngược (destination, origin) xem có không,
    #   nếu cũng không có -> "Không tìm thấy chuyến bay từ X đến Y."
    # - Gợi ý: format giá tiền có dấu chấm phân cách (1.450.000đ)

    key = (origin, destination)
    reverse_key = (destination, origin)

    flights = FLIGHTS_DB.get(key)

    if not flights:
        flights = FLIGHTS_DB.get(reverse_key)
        if not flights:
            return f"Không tìm thấy chuyến bay từ {origin} đến {destination}."
        else:
            direction_note = f"(Không có chuyến trực tiếp, hiển thị chiều ngược lại {destination} → {origin})\n"
    else:
        direction_note = ""

    result = [f"Danh sách chuyến bay {origin} → {destination}:"]

    for f in flights:
        airline = f.get("airline", "N/A")
        time = f.get("time", "N/A")
        price = format_currency(f.get("price", 0))

        result.append(f"- {airline} | Giờ bay: {time} | Giá: {price}")

    return direction_note + "\n".join(result)

@tool
def search_hotels(city: str, max_price_per_night: int = 99999999) -> str:
    """
    Tìm kiếm khách sạn tại một thành phố, có thể lọc theo giá tối đa mỗi đêm.
    Tham số:
    - city: tên thành phố (VD: 'Đà Nẵng', 'Phú Quốc', 'Hồ Chí Minh')
    - max_price_per_night: giá tối đa mỗi đêm (VNĐ), mặc định không giới hạn
    Trả về danh sách khách sạn phù hợp với tên, số sao, giá, khu vực, rating.
    """
    # TODO: Sinh viên tự triển khai
    # - Tra cứu HOTELS_DB[city]
    # - Lọc theo max_price_per_night
    # - Sắp xếp theo rating giảm dần
    # - Format đẹp. Nếu không có kết quả -> "Không tìm thấy khách sạn tại X 
    #   với giá dưới Y/đêm. Hãy thử tăng ngân sách."

    hotels = HOTELS_DB.get(city, [])
    filtered_hotels = [h for h in hotels if h.get("price_per_night", 0) <= max_price_per_night]
    if not filtered_hotels:
        return f"Không tìm thấy khách sạn tại {city} với giá dưới {format_currency(max_price_per_night)}/đêm. Hãy thử tăng ngân sách."
    
    sorted_hotels = sorted(filtered_hotels, key=lambda x: x.get("rating", 0), reverse=True)
    
    result = [f"Danh sách khách sạn tại {city}:"]
    for h in sorted_hotels:
        name = h.get("name", "N/A")
        stars = h.get("stars", "N/A")
        area = h.get("area", "N/A")
        rating = h.get("rating", "N/A")
        price = format_currency(h.get("price_per_night", 0))
        result.append(f"- {name} ({stars} sao) | Khu vực: {area} | Đánh giá: {rating} | Giá: {price}/đêm")
        
    return "\n".join(result)

@tool
def calculate_budget(total_budget: int, expenses: str) -> str:
    """
    Tính toán ngân sách còn lại sau khi trừ các khoản chi phí.
    Tham số:
    - total_budget: tổng ngân sách ban đầu (VNĐ)
    - expenses: chuỗi mô tả các khoản chi, mỗi khoản cách nhau bởi dấu phẩy, 
      định dạng 'tên_khoản:số_tiền' (VD: 'vé_máy_bay:890000,khách_sạn:650000')
    Trả về bảng chi tiết các khoản chi và số tiền còn lại.
    Nếu vượt ngân sách, cảnh báo rõ ràng số tiền thiếu.
    """
    # TODO: Sinh viên tự triển khai
    # - Parse chuỗi expenses thành dict {tên: số_tiền}
    # - Tính tổng chi phí
    # - Tính số tiền còn lại = total_budget - tổng chi phí
    # - Format bảng chi tiết:
    #   Bảng chi phí:
    #   - Vé máy bay: 890.000đ
    #   - Khách sạn: 650.000đ
    #   ---
    #   Tổng chi: 1.540.000đ
    #   Ngân sách: 5.000.000đ
    #   Còn lại: 3.460.000đ
    # - Nếu âm -> "Vượt ngân sách X đồng! Cần điều chỉnh."
    # - Xử lý lỗi: nếu expenses format sai -> trả về thông báo lỗi rõ ràng

    try:
        expense_dict = {}
        if expenses.strip():
            for item in expenses.split(','):
                if ':' not in item:
                    raise ValueError("Thiếu dấu ':' phân cách")
                name, amount_str = item.split(':', 1)
                expense_dict[name.strip()] = int(amount_str.strip())
    except Exception as e:
        return "Lỗi format expenses."

    total_expense = sum(expense_dict.values())
    remaining = total_budget - total_expense

    result = ["Bảng chi phí:"]
    for name, amount in expense_dict.items():
        display_name = name.replace('_', ' ').capitalize()
        result.append(f"- {display_name}: {format_currency(amount)}")
        
    result.append("---")
    result.append(f"Tổng chi: {format_currency(total_expense)}")
    result.append(f"Ngân sách: {format_currency(total_budget)}")
    
    if remaining >= 0:
        result.append(f"Còn lại: {format_currency(remaining)}")
    else:
        result.append(f"Còn lại: -{format_currency(abs(remaining))}")
        result.append(f"Vượt ngân sách {format_currency(abs(remaining))}! Cần điều chỉnh.")
        
    return "\n".join(result)
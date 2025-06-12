import requests
import time
import json
from datetime import datetime

API_URL = "https://show.bilibili.com/api/ticket/project/getV2?version=134&id=102194&project_id=102194"
CHECK_INTERVAL = 5  # 检查间隔(秒)
GOTIFY_URL = "https://localhost:8080"  # 为你的Gotify服务器地址
GOTIFY_TOKEN = ""  # 为你的Gotify应用token
last_status = None
last_check_time = None

def get_ticket_status():
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Referer": "https://show.bilibili.com/",
            "Origin": "https://show.bilibili.com"
        }
        response = requests.get(API_URL, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get("data", {}).get("sale_flag", "未知状态")
    except Exception as e:
        print(f"获取票务状态失败: {e}")
        return None

def send_gotify_notification(message):
    try:
        data = {
            "message": message,
            "priority": 8,
            "title": "BW2025票务状态变化",
            "extras": {
                "client::notification": {
                    "click": {
                        "url": "bilibili://mall/web?url=https://mall.bilibili.com/mall-dayu/neul-next/ticket/detail.html?id=102194"
                    }
                }
            }
        }
        headers = {
            "Content-Type": "application/json"
        }
        response = requests.post(
            f"{GOTIFY_URL}?token={GOTIFY_TOKEN}",
            data=json.dumps(data),
            headers=headers,
            timeout=10
        )
        response.raise_for_status()
        print("通知发送成功")
    except Exception as e:
        print(f"发送Gotify通知失败: {e}")

def monitor_ticket_status():
    global last_status, last_check_time
    
    print("开始监控BW2025票务状态...")
    print(f"检查频率: 每{CHECK_INTERVAL}秒一次")
    
    while True:
        current_status = get_ticket_status()
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if current_status is None:
            print(f"{current_time} - 获取状态失败，等待下一次检查...")
            time.sleep(CHECK_INTERVAL)
            continue
        
        print(f"{current_time} - 当前状态: {current_status}")
        
        if last_status is None:
            last_status = current_status
            last_check_time = current_time
        elif current_status != last_status:
            print(f"状态变化: {last_status} -> {current_status}")
            
            if (last_status == "不可售" and current_status != "不可售") or \
               (last_status in ["已售罄", "暂时售罄"] and current_status == "预售中"):
                message = f"BW2025票务状态变化: {last_status} → {current_status},点击跳转到哔哩哔哩APP。"
                send_gotify_notification(message)
            last_status = current_status
            last_check_time = current_time
        
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    monitor_ticket_status()
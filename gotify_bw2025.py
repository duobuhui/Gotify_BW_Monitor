import requests
import time
import json
from datetime import datetime

# 配置常量
PROJECT_IDS = {"BW": "102194", "BML": "102626"} 
<<<<<<< HEAD
CHECK_INTERVAL = 5  # 检查间隔(秒)
GOTIFY_URL = "http://localhost:8080"  # Gotify服务器地址
GOTIFY_TOKEN = ""  # Gotify应用token
=======
PROJECT_NAMES = {"102194": "BW", "102626": "BML"}  # 新增项目ID到名称的映射
CHECK_INTERVAL = 1  # 检查间隔(秒)
GOTIFY_URL = "http://localhost:8080"  # Gotify服务器地址
GOTIFY_TOKEN = "Apq--PMSLTGCNsV"  # Gotify应用token
>>>>>>> parent of 8c2c87c (自定义通知信息)

def get_ticket_status(project_id):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Referer": f"https://show.bilibili.com/platform/detail.html?id={project_id}",
            "Origin": "https://show.bilibili.com",
            "Accept": "application/json",
            "X-Requested-With": "XMLHttpRequest"
        }
        
        response = requests.get(
            "https://show.bilibili.com/api/ticket/project/getV2",
            headers=headers,
            params={
                "version": "134",
                "id": project_id,
                "project_id": project_id
            },
            timeout=15  
        )
        
        response.raise_for_status()
        json_data = response.json()
        
        if not json_data.get("data"):
            print(f"响应中缺少data字段，完整响应: {json_data}")
            return None
            
        return json_data["data"]
        
    except requests.exceptions.RequestException as e:
        print(f"请求失败: {str(e)[:100]}")  
        return None
    except ValueError as e:
        print(f"JSON解析失败: {e}")
        return None

def send_gotify_notification(project_id, project_name, message):
    try:
        response = requests.post(
            f"{GOTIFY_URL}/message?token={GOTIFY_TOKEN}",
            json={  
                "message": message,
                "priority": 8,
                "title": f"{project_name}票务状态变化，可能是有票啦！",  # 修改标题
                "extras": {
                    "client::notification": {
                        "click": {
                            "url": f"bilibili://mall/web?url=https://mall.bilibili.com/mall-dayu/neul-next/ticket/detail.html?id={project_id}"
                        }
                    }
                }
            },
            timeout=10
        )
        response.raise_for_status()
        print("通知发送成功")
    except Exception as e:
        print(f"发送Gotify通知失败: {str(e)[:100]}")

def format_status_info(data):
    if not data:
        return None
        
    return {
        "sale_flag": data.get("sale_flag", "未知状态"),
        "sale_start": datetime.fromtimestamp(data.get("sale_start", 0)).strftime("%Y-%m-%d %H:%M:%S"),
        "price_low": f"{data.get('price_low', 0) / 100:.2f}元", 
        "screens": [
            {
                "name": screen.get("name", "未知场次"),
                "status": screen.get("saleFlag", {}).get("display_name", "未知状态")
            }
            for screen in data.get("screen_list", [])
        ]
    }

def print_status_info(current_time, status_info):
    print(f"\n{current_time} - 票务状态:")
    print(f"主状态: {status_info['sale_flag']}")
    print(f"开售时间: {status_info['sale_start']}")
    print(f"最低价格: {status_info['price_low']}")
    print("场次状态:")
    for screen in status_info["screens"]:
        print(f"  - {screen['name']}: {screen['status']}")

def monitor_ticket_status():
    """监控票务状态"""
    print("可选项目:", ", ".join(f"{k}:{v}" for k,v in PROJECT_IDS.items()))
    project_input = input("请输入项目ID或名称: ").strip()
    
    # 获取项目ID和名称
    if project_input.upper() in PROJECT_IDS:
        project_id = PROJECT_IDS[project_input.upper()]
        project_name = project_input.upper()
    else:
        project_id = project_input
        project_name = PROJECT_NAMES.get(project_id, "项目")  # 默认使用"项目"如果找不到名称
    
    print(f"\n开始监控票务状态(项目: {project_name}, ID: {project_id})...")
    print(f"检查频率: 每{CHECK_INTERVAL}秒一次")
    
    last_status = None
    error_count = 0
    MAX_ERRORS = 5
    first_run = True  
    
    try:
        while True:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            data = get_ticket_status(project_id)
            
            if data is None:
                error_count += 1
                print(f"{current_time} - 获取状态失败({error_count}/{MAX_ERRORS})")
                if error_count >= MAX_ERRORS:
                    print("连续多次失败，暂停监控...")
                    break
                time.sleep(CHECK_INTERVAL)
                continue
            
            error_count = 0
            status_info = format_status_info(data)
            
            if not status_info:
                print(f"{current_time} - 数据格式异常")
                time.sleep(CHECK_INTERVAL)
                continue
            
            print_status_info(current_time, status_info)
            
            if first_run or (last_status and status_info['sale_flag'] != last_status['sale_flag']):
                message = f"""
                {'🔄 首次状态检测 🔄' if first_run else '⚠️ 票务状态变化 ⚠️'}
--------------------------
项目: {project_name} (ID: {project_id})
{'当前状态' if first_run else '旧状态'}: {last_status['sale_flag'] if last_status and not first_run else status_info['sale_flag']}
{'新状态: ' + status_info['sale_flag'] if not first_run else ''}
开售时间: {status_info['sale_start']}
--------------------------
                """ 
                
                print("\n检测到状态变化，发送通知..." if not first_run else "\n首次检测，发送通知...")
                send_gotify_notification(project_id, project_name, message.strip())  # 传递project_name参数
                first_run = False
            
            last_status = status_info
            time.sleep(CHECK_INTERVAL)
            
    except KeyboardInterrupt:
        print("\n监控已手动停止")

if __name__ == "__main__":
    monitor_ticket_status()
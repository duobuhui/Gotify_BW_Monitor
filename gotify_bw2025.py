import requests
import time
import json
from datetime import datetime

PROJECT_IDS = {"BW": "102194", "BML": "102626"} 
CHECK_INTERVAL = 5  # 检查间隔(秒)
GOTIFY_URL = "http://49.234.25.178:8080"  # Gotify服务器地址
GOTIFY_TOKEN = "Apq--PMSLTGCNsV"  # Gotify应用token

# 自定义通知
NOTIFICATION_TEMPLATE = {
    "title": "{project_name}有票啦！c",  # 标题
    "message": """
    项目: {project_name}
    状态: {old_status} → {new_status}
    开售时间: {sale_start}
    最低价格: {price_low}元
    监控场次: {monitored_screens}
    --------------------------
    {status_emoji} {status_change_text}
    """,  # 消息内容
    "priority": 8  # 通知优先级
}

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

def send_gotify_notification(project_id, project_name, message_data, monitored_screens):
    try:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        title = NOTIFICATION_TEMPLATE["title"].format(
            project_name=project_name,
            current_time=current_time
        )
        
        relevant_screens = []
        for screen in message_data["screens"]:
            if screen["name"] in monitored_screens:
                relevant_screens.append(f"{screen['name']}: {screen['status']}")
        
        message = NOTIFICATION_TEMPLATE["message"].format(
            status_emoji="🔄" if message_data["is_first_run"] else "⚠️",
            status_change_text="首次状态检测" if message_data["is_first_run"] else "票务状态变化",
            project_name=project_name,
            old_status=message_data["old_status"],
            new_status=message_data["new_status"],
            sale_start=message_data["sale_start"],
            price_low=message_data["price_low"],
            monitored_screens=", ".join(relevant_screens) if relevant_screens else "无",
            current_time=current_time
        )
        
        response = requests.post(
            f"{GOTIFY_URL}/message?token={GOTIFY_TOKEN}",
            json={  
                "message": message.strip(),
                "priority": NOTIFICATION_TEMPLATE["priority"],
                "title": title,
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
        
    screens_info = []
    for screen in data.get("screen_list", []):
        screen_name = screen.get("name", "未知场次")
        screen_status = screen.get("saleFlag", {}).get("display_name", "未知状态")
        
        screens_info.append({
            "name": screen_name,
            "status": screen_status,
            "id": screen.get("id")
        })
    
    return {
        "project_name": data.get("name", "未知项目"),  
        "sale_flag": data.get("sale_flag", "未知状态"),
        "sale_start": datetime.fromtimestamp(data.get("sale_start", 0)).strftime("%Y-%m-%d %H:%M:%S"),
        "price_low": data.get("price_low", 0) / 100,
        "screens": screens_info,
        "sale_flag_number": data.get("sale_flag_number", 0)
    }

def print_status_info(current_time, status_info):
    print(f"\n{current_time} - 票务状态:")
    print(f"项目名称: {status_info['project_name']}")
    print(f"主状态: {status_info['sale_flag']} (代码: {status_info['sale_flag_number']})")
    print(f"开售时间: {status_info['sale_start']}")
    print(f"最低价格: {status_info['price_low']:.2f}元")
    print("所有场次状态:")
    for screen in status_info["screens"]:
        print(f"  - {screen['name']}: {screen['status']}")

def select_screens_to_monitor(available_screens):
    print("\n可用的场次列表:")
    for i, screen in enumerate(available_screens, 1):
        print(f"{i}. {screen['name']} (当前状态: {screen['status']})")
    
    print("\n请选择要监控的场次(输入编号，多个用逗号分隔，全部监控输入'all'):")
    selection = input("> ").strip()
    
    if selection.lower() == 'all':
        return [screen['name'] for screen in available_screens]
    
    selected_indices = []
    for s in selection.split(','):
        try:
            index = int(s.strip()) - 1
            if 0 <= index < len(available_screens):
                selected_indices.append(index)
        except ValueError:
            continue
    
    return [available_screens[i]['name'] for i in selected_indices] if selected_indices else []

def monitor_ticket_status():
    print("可选项目:", ", ".join(f"{k}:{v}" for k,v in PROJECT_IDS.items()))
    project_input = input("请输入项目ID或名称: ").strip()
    
    if project_input.upper() in PROJECT_IDS:
        project_id = PROJECT_IDS[project_input.upper()]
    else:
        project_id = project_input
    
    initial_data = get_ticket_status(project_id)
    if not initial_data:
        print("无法获取项目信息，请检查项目ID是否正确")
        return
    
    status_info = format_status_info(initial_data)
    if not status_info:
        print("无法解析项目信息")
        return
    
    project_name = status_info["project_name"]
    print(f"\n项目名称: {project_name}")
    print_status_info(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), status_info)
    
    monitored_screens = select_screens_to_monitor(status_info["screens"])
    if not monitored_screens:
        print("未选择任何场次，将只监控整体状态变化")
    
    print(f"\n开始监控票务状态(项目: {project_name}, ID: {project_id})...")
    if monitored_screens:
        print(f"监控的场次: {', '.join(monitored_screens)}")
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
            
            status_changed = first_run or (last_status and status_info['sale_flag'] != last_status['sale_flag'])
            
            if not status_changed and monitored_screens and last_status:
                for screen in status_info["screens"]:
                    if screen["name"] in monitored_screens:
                        old_screen = next((s for s in last_status["screens"] if s["name"] == screen["name"]), None)
                        if old_screen and screen["status"] != old_screen["status"]:
                            status_changed = True
                            break
            
            if status_changed:
                message_data = {
                    "is_first_run": first_run,
                    "old_status": last_status['sale_flag'] if last_status and not first_run else status_info['sale_flag'],
                    "new_status": status_info['sale_flag'],
                    "sale_start": status_info['sale_start'],
                    "price_low": status_info['price_low'],
                    "screens": status_info["screens"]
                }
                
                print("\n检测到状态变化，发送通知..." if not first_run else "\n首次检测，发送通知...")
                send_gotify_notification(project_id, project_name, message_data, monitored_screens)
                first_run = False
            
            last_status = status_info
            time.sleep(CHECK_INTERVAL)
            
    except KeyboardInterrupt:
        print("\n监控已手动停止")

if __name__ == "__main__":
    monitor_ticket_status()
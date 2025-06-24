## Gotify_BW_Monitor
### 简介
本程序监控B站会员购票务，使用 [Gotify](https://github.com/gotify) 推送票务状态，如票档更新，回流票放出事件。在 [Gotify](https://github.com/gotify) 手机APP上，将可以点击通知一步直达购票页面。

感谢微信小程序易票哒，让作者发现了 [Gotify](https://github.com/gotify) 在抢票上的应用。（你怎么知道我用这个方法抢到了方舟和崩铁音乐会的回流票）

由于期末周，程序由AI大模型 [deepseek](https://www.deepseek.com/) 辅助完成。

### 使用方式
在开始下面的步骤前，你需要拥有 [Gotify](https://github.com/gotify) 服务器地址，自行设定的账号密码和`gotify token`。你可以通过自建服务器，或使用公益服务器的方式获得。

1. 安装依赖
```
pip install requests
```
2. 编辑程序的第 8、9 行，填入你的服务器地址和`gotify token`。

3. 运行程序
```
python gotify_bw2025.py
```
4. 填入你需要监控的项目 id，不仅限于 BW/BML，但非 BW/BML 可能会出现问题。然后根据程序指引选择监控的场次，以逗号分隔，输入all则全部监控。
程序会在首次运行时发送一次通知，以便于调试 Gotify 手机 APP。

5. 保持程序开启的状态下，就可以将 APP 置于后台，检测到状态更新时会通知你。只需要点击通知，就可以直接跳转到哔哩哔哩 APP 内购票页。

### 自定义推送信息
现在你可以自定义推送信息了，我在程序中预留了一些变量以供使用。标题修改在第13行的引号内，消息内容修改在第14行至22行的三引号内。
#### 可用变量
- `{status_emoji}` - 🔄 表示首次检测，⚠️ 表示状态变化，可在78行修改
- `{status_change_text}` - "首次状态检测" 或 "票务状态变化"，可在79行修改
- `{project_name}` - 项目完整名称
- `{old_status}` - 旧的状态 (首次检测时与new_status相同)
- `{new_status}` - 新的状态
- `{sale_start}` - 开售时间 (格式: YYYY-MM-DD HH:MM:SS)
- `{price_low}` - 最低票价 (单位: 元)
- `{monitored_screens}` - 用户选择的监控场次及状态
- `{current_time}` - 当前检测时间 (格式: YYYY-MM-DD HH:MM:SS)

#### 高级变量 (需修改代码)
如需更多数据，可以修改 `format_status_info` 函数提取以下额外数据：
- `{price_high}` - 最高票价
- `{venue}` - 场馆名称
- `{sale_end}` - 售票结束时间
- `{screen_count}` - 总场次数
- `{project_id}` - 项目ID

### 常见问题
1. Gotify APP 常驻通知不为`Connected`:
- 请注意在手机设置中，调整 Gotify APP 的电源优化为不允许，允许 Gotify APP 后台运行和自启动。

2. 票务信息变化 通知不展示为横幅:
- 请在手机设置，Gotify APP 通知管理中，将 `High priority messages(>7)` 的横幅通知打开。你也可以自行设定，调整程序第 55 行的`priority`值。

3. Gotify APP 通知为`Connected`，但不能实时接收通知：
- 建议尝试重启手机，重装 APP 等操作。可以在 APP 左上角三条杠选择 Log，查看 WebSocket 是否断开连接。

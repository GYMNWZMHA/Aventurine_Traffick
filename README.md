# 砂金自动贩卖机 (Aventurine Traffick)

> **免责声明**：本脚本仅供学习交流使用，严禁用于商业用途。使用本脚本产生的任何后果由使用者自行承担，作者不承担任何责任。请遵守游戏规则，合理使用。

## 使用说明

### ① 通用提示手册

1. 安装 Python 以及配置环境。
2. 终端输入以下代码安装依赖库：
    ```shell
    pip install pyautogui mss opencv-python numpy keyboard pywin32 colorama
    ```
    或
    ```shell
    pip install -r requirements.txt
    ```
    清华镜像:
    ```shell
    pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
    ```
3. 下载 VS Code 以及 Python 扩展。
4. 使用目标为游戏《崩坏·星穹铁道》4.2版本的货币战争模式「沙里淘金」玩法。
5. 使用前需先将 VS Code 窗口放至左下角，将游戏的两个空备战位放至右侧，最好至少留等效一个一星的砂金。
6. 点击运行脚本，同意管理员权限开始。
7. 紧急停止脚本的默认按键是 `Ctrl+Shift+Z`，请在使用前注意是否和其他软件的快捷按键冲突。
8. 演示视频：https://b23.tv/BV1medaByE2Y

### ② 适用于 LTS 版本的提示

- 该版本目前只支持 `3072×1920` 的屏幕分辨率。

### ③ 个性化程序

1. **定位配置生成函数**  
   打开主程序，找到第87行附近的 `def generate_default_config():` 函数。

2. **修改屏幕分辨率**  
   找到 `"screen"` 项，将 `width` 和 `height` 改为您显示器的实际分辨率。  
   示例：`"screen": {"width": 1920, "height": 1080}`

3. **配置刷新按钮（click_set_A 中的 name: "0"）**  
   仅需修改 `"click"` 的 `x` 和 `y` 值，设置为游戏内刷新按钮的点击坐标。  
   示例：`"click": {"x": 2611, "y": 768}`

4. **配置商店槽位（click_set_A 中的 name: "1" ~ "5"）**  
   每个槽位包含两组数据：
   - `capture_region`（截图范围）  
     `x, y`：截图区域左上角坐标。  
     `w, h`：截图宽度和高度。  
     要求：截图范围应大致覆盖目标卡牌，使模板 `target_M` 能匹配。  
     技巧：五个槽位的 `w` 和 `h` 通常一致；`x` 和 `y` 呈等差数列。
   - `click`（点击坐标）  
     `x, y`：购买时鼠标点击的位置。  
     建议：将 `y` 设置为略小于 `capture_region` 的 `y`，避免鼠标遮挡截图。

5. **模板图片的命名与准备**  
   此程序需要多张模板图片，您可以根据分辨率自行截图并重命名。
   - `template_image_M`：商店中待购买的目标卡牌 `target_M.png`，截图范围参考商店槽位。
   - `template_image_L1`：备战席1星卡牌 `target_L1_3k.png`，截取备战席中1星卡牌。
   - `template_image_L2`：备战席2星卡牌 `target_L2_3k.png`，截取备战席中2星卡牌。
   - `template_image_L3`：备战席3星卡牌 `target_L3_3k.png`，截取备战席中3星卡牌。
   - `template_image_S1`：临时备战席（U区）1星卡牌 `target_S1_3k.png`，截取U区中1星卡牌。
   - `template_image_Sx`：临时备战席（U区）红底背景 `target_Sx_3k.png`，截取U区中的红底背景。  
   右侧的 `*.png` 可改为您自定义的文件名，但必须与配置中的名称一致。原有适配3K的示例图片可删除。

6. **配置备战区识别区域（count_regions）**  
   - `DL`：备战席左侧一格
   - `DR`：备战席右侧一格
   - `U`：临时备战席（合成时出现的额外槽位）  
   每个区域需要填写 `x, y`（左上角顶点）和 `w, h`（宽高）。  
   操作：截取对应卡牌所在矩形区域，记录坐标填入。

7. **配置拖动出售（drag_set_B）**  
   - `from`：拖动起点坐标（通常位于 `DL` 区域范围内）。
   - `to`：拖动终点坐标（松开鼠标后触发售卖的区域）。

8. **其他参数典型值**（以上没提及的一般保持默认）  
   - `similarity_threshold`：匹配相似度阈值
   - `hotkey_stop`：停止脚本的热键。
     - 该项用于在 `generate_default_config` 函数中创建默认的停止热键 `"ctrl+shift+z"`，您可修改此值为自定义的热键组合
     - 脚本在 `init_config_and_templates` 函数中会从配置文件里查找 `hotkey_stop` 项。如果由于配置缺失或修改不当导致该项不存在，程序会自动将其替换为 `"ctrl+shift+x"` 以保证脚本能被正常终止。这可以在一定程度上预防因与系统热键冲突而导致默认热键失效的问题
   - `drag_poll_interval`：拖动前轮询间隔
   - `max_rounds`：自动重启轮次
   - `drag_max_wait`：拖动前最大等待时间

9. **获取坐标的小技巧**  
   截取游戏窗口，粘贴到画图软件中，移动鼠标可查看坐标。  
   商店五个槽位的 `x` 通常等间距，可先测第一个和最后一个，再平均分配中间值。

## 许可证

本代码采用 [Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0)](https://creativecommons.org/licenses/by-nc-sa/4.0/) 许可证。您可以自由分享、修改本代码，但必须署名、不得用于商业目的，且修改后的作品必须以相同许可证发布。
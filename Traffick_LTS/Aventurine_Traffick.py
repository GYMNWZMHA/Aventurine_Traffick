import os
import json
import sys
import time
import pyautogui
import mss
import cv2
import numpy as np
import ctypes
import keyboard
from concurrent.futures import ThreadPoolExecutor, as_completed
import win32gui
import win32console
import win32con
from colorama import init, Fore, Back, Style
import threading
from queue import Queue

# ========== 底层设置 ==========

# 颜色
init(autoreset=True)

# 提权
def run_as_admin():
    try:
        is_admin = ctypes.windll.shell32.IsUserAnAdmin()
    except:
        is_admin = False
    if not is_admin:
        script_path = os.path.abspath(sys.argv[0])
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, f'"{script_path}"', None, 1)
        sys.exit(0)
run_as_admin()

# 位置
def set_console_window_topmost(x=None, y=None, width=None, height=None):
    console_hwnd = win32console.GetConsoleWindow()
    if console_hwnd == 0:
        print(Back.RED + "无法获取控制台窗口句柄，请确保在控制台环境下运行。")
        return
    rect = win32gui.GetWindowRect(console_hwnd)
    current_x, current_y, current_right, current_bottom = rect
    current_width = current_right - current_x
    current_height = current_bottom - current_y
    new_x = x if x is not None else current_x
    new_y = y if y is not None else current_y
    new_width = width if width is not None else current_width
    new_height = height if height is not None else current_height
    win32gui.SetWindowPos(console_hwnd, win32con.HWND_TOPMOST,
                          new_x, new_y, new_width, new_height,
                          win32con.SWP_SHOWWINDOW)
    print(Back.GREEN + f"控制台窗口已置顶，位置：({new_x}, {new_y})，大小：{new_width}x{new_height}")
set_console_window_topmost(x=700, y=620, width=1000, height=1300)



# ========== 全局配置 ==========

# 净赚
script_dir = os.path.dirname(os.path.abspath(__file__))
GLOBAL_COUNTER_FILE = os.path.join(script_dir, "global_counter.json")
def load_global_counter():
    if os.path.exists(GLOBAL_COUNTER_FILE):
        with open(GLOBAL_COUNTER_FILE, 'r') as f:
            data = json.load(f)
            return data.get("counter", 0)
    return 0
def save_global_counter(value):
    with open(GLOBAL_COUNTER_FILE, 'w') as f:
        json.dump({"counter": value}, f)

# 计时
ACCUMULATED_FILE = os.path.join(script_dir, "accumulated.json")
def load_accumulated():
    if os.path.exists(ACCUMULATED_FILE):
        with open(ACCUMULATED_FILE, 'r') as f:
            data = json.load(f)
            return data.get("total_sec", 0), data.get("total_net", 0)
    return 0, 0
def save_accumulated(total_sec, total_net):
    with open(ACCUMULATED_FILE, 'w') as f:
        json.dump({"total_sec": total_sec, "total_net": total_net}, f)

# 配置
config_file = os.path.join(script_dir, "config.json")
try:
    with open(config_file, 'r', encoding='utf-8') as f:
        config = json.load(f)
except Exception as e:
    print(f'加载配置文件时出错: {e}')

def generate_default_config():
    default_config = {
        "screen": {"width": 3072, "height": 1920},
        "click_set_A": [
            {"name": "0", "capture_region": {"x": 2585, "y": 835, "w": 122, "h": 159}, "click": {"x": 2611, "y": 768, "delay": 0.5}},
            {"name": "1", "capture_region": {"x": 602, "y": 319, "w": 364, "h": 217}, "click": {"x": 921, "y": 192, "delay": 0.15}},
            {"name": "2", "capture_region": {"x": 1033, "y": 319, "w": 364, "h": 217}, "click": {"x": 1228, "y": 192, "delay": 0.15}},
            {"name": "3", "capture_region": {"x": 1463, "y": 319, "w": 364, "h": 217}, "click": {"x": 1536, "y": 192, "delay": 0.15}},
            {"name": "4", "capture_region": {"x": 1892, "y": 319, "w": 364, "h": 217}, "click": {"x": 2150, "y": 192, "delay": 0.15}},
            {"name": "5", "capture_region": {"x": 2323, "y": 319, "w": 364, "h": 217}, "click": {"x": 2457, "y": 192, "delay": 0.15}}
        ],
        "template_image_M": "target_M.png",
        "template_image_L1": "target_L1_3k.png",
        "template_image_L2": "target_L2_3k.png",
        "template_image_L3": "target_L3_3k.png",
        "template_image_S1": "target_S1_3k.png",
        "template_image_Sx": "target_Sx_3k.png",
        "count_regions": [
            {"name": "DL", "x": 2055, "y": 1684, "w": 80, "h": 28},
            {"name": "DR", "x": 2255, "y": 1684, "w": 80, "h": 28},
            {"name": "U",  "x": 2173, "y": 1319, "w": 121, "h": 140}
        ],
        "similarity_threshold": 0.8,
        "drag_set_B": {"from": {"x": 2100, "y": 1600}, "to": {"x": 2900, "y": 1600}, "duration": 0.15},
        "hotkey_stop": "ctrl+shift+z",
        "drag_poll_interval": 0.4,
        "max_rounds": 30,
        "drag_max_wait": 3.5
    }
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(default_config, f, ensure_ascii=False, indent=4)
    print(Back.GREEN + f"已生成默认配置文件：{config_file}")
    return True

# 检验
def ensure_file():
    if not os.path.exists(GLOBAL_COUNTER_FILE):
        print(Back.RED + "未找到 global_counter.json，正在尝试生成累计净赚文件")
        save_global_counter(0)
    else:
        print(Back.GREEN + "累计净赚文件校验完毕")
    if not os.path.exists(ACCUMULATED_FILE):
        save_accumulated(0, 0)
        print(Back.RED + "未找到 accumulated.json，正在尝试生成累计计时文件")
    else:
        print(Back.GREEN + "累计计时文件校验完毕")
    if not os.path.exists(config_file):
        print(Back.RED + "未找到 config.json，正在尝试生成默认配置文件")
        generate_default_config()
    else:
        print(Back.GREEN + "默认配置文件校验完毕")
ensure_file()

command_queue = Queue()
hotkey_pause: str | None = None
hotkey_stop: str | None = None

def hotkey_listener():
    """独立线程监听热键"""
    global hotkey_pause
    global hotkey_stop
    def on_pause():
        command_queue.put('pause')
        print("\n[热键] 暂停命令已接收")
    def on_stop():
        command_queue.put('stop')
        print("\n[热键] 暂停命令已接收")

    hotkey_pause = config.get('hotkey_pause', 'ctrl+shift+p')
    hotkey_stop = config.get('hotkey_stop', 'ctrl+shift+z')

    try:
        # 注册全局热键
        keyboard.add_hotkey(hotkey_pause, on_pause)
        keyboard.add_hotkey(hotkey_stop, on_stop)

        print(Back.GREEN + f"已注册暂停热键：{hotkey_pause}")
        print(Back.GREEN + f"已注册停止热键：{hotkey_stop}")
    except Exception as e:
        print(Back.RED + f"热键注册失败: {e}")
        exit(-1)

    # 保持线程运行
    keyboard.wait()

# 导入
def init_config_and_templates():
    global stop_requested

    os.chdir(script_dir)
    print(Back.GREEN + f"当前工作目录：{os.getcwd()}")

    screen_w, screen_h = pyautogui.size()
    print(Back.GREEN + f"检测到屏幕分辨率：{screen_w}x{screen_h}")

    click_set_A = config['click_set_A']
    template_path_M = config.get('template_image_M', 'target_M.png')
    template_path_L1 = config.get('template_image_L1', 'target_L1_3k.png')
    template_path_L2 = config.get('template_image_L2', 'target_L2_3k.png')
    template_path_L3 = config.get('template_image_L3', 'target_L3_3k.png')
    template_path_S1 = config.get('template_image_S1', 'target_S1_3k.png')
    template_path_Sx = config.get('template_image_Sx', 'target_Sx_3k.png')
    similarity_threshold = config.get('similarity_threshold', 0.8)
    drag_set_B = config['drag_set_B']
    drag_poll_interval = config.get('drag_poll_interval', 0.2)
    drag_max_wait = config.get('drag_max_wait', 3.0)
    count_regions = config.get('count_regions', [])
    MAX_ROUNDS = config.get('max_rounds', 100)

    # 预加载模板
    def load_template(path, name):
        if os.path.exists(path):
            img = cv2.imread(path)
            if img is None:
                print(Back.RED + f"警告：无法读取 {path}，{name} 将失效")
                return None
            return img
        else:
            print(Back.RED + f"警告：{path} 不存在，{name} 将失效")
            return None

    template_M = load_template(template_path_M, "商店识别")
    template_L1 = load_template(template_path_L1, "1星")
    template_L2 = load_template(template_path_L2, "2星")
    template_L3 = load_template(template_path_L3, "3星")
    template_S1 = load_template(template_path_S1, "特殊1星")
    template_Sx = load_template(template_path_Sx, "特殊x星")

    if not isinstance(MAX_ROUNDS, int) or MAX_ROUNDS <= 0:
        MAX_ROUNDS = 100
        print(Back.RED + "警告：max_rounds 配置无效，已重置为 100")

    return (click_set_A, template_M, template_L1, template_L2, template_L3,
            template_S1, template_Sx, similarity_threshold, drag_set_B, drag_poll_interval,
            drag_max_wait, count_regions, MAX_ROUNDS)

# 守门员
global_counter = load_global_counter()
total_sec, total_net = load_accumulated()
def hello():
    if global_counter == 0 and total_sec == 0 and total_net == 0:
        time.sleep(1)
        print("")
        print(Back.LIGHTGREEN_EX + "欢迎使用砂金自动贩卖机")
        print(Back.CYAN + "爱来自bilibili@甘雨没你我怎么活啊")
        print(Back.LIGHTRED_EX + "若您因此支付了任何费用，那么证明您被骗了")
        print("")
        print(Fore.GREEN + "该颜色为正向提示")
        print(Fore.YELLOW + "该颜色为负面提示，出现此类问题可能影响到效率")
        print(Fore.RED + "该颜色为可能致命的错误，出现此类问题可能导致循环逻辑紊乱")
        print(Back.GREEN + "该颜色为系统配置成功")
        print(Back.RED + "该颜色为系统配置失败，出现此类问题可能导致程序崩溃，建议重启以尝试解决或联系至作者寻求帮助")
        print(Fore.BLUE + "该颜色为常数提示")
        print(Back.BLUE + "该颜色为全局常数提示")
        start_sleep = 5
        print(Fore.GREEN + f"{start_sleep}秒后正式启动")
        time.sleep(start_sleep)
def say_hello():
    if os.path.exists(GLOBAL_COUNTER_FILE) and os.path.exists(ACCUMULATED_FILE) and os.path.exists(config_file):
        hello()
    else:
        ensure_file()
        print(Back.RED + "已尝试恢复，如有异常请立刻终止程序")
        hello()



# ========== 函数单元 ==========

# 停止
stop_requested = False
last_stop_trigger = 0
def stop_script():
    global last_stop_trigger, stop_requested
    now = time.monotonic()
    if now - last_stop_trigger < 1.0:
        return
    last_stop_trigger = now
    stop_requested = True
    print(Back.GREEN + "收到停止信号...")

# 截图
def capture_region(region_ratio):
    try:
        with mss.mss() as sct:
            monitor = {
                'left': region_ratio['x'],
                'top': region_ratio['y'],
                'width': region_ratio['w'],
                'height': region_ratio['h']
            }
            img = sct.grab(monitor)
            img = np.array(img)
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
            return img
    except Exception as e:
        print(Fore.RED + f"截图失败: {e}")
        return np.zeros((1, 1, 3), dtype=np.uint8)

# 目标
def match_template(screenshot, template_img, threshold=0.8):
    if template_img is None:
        return False, 0.0
    try:
        if screenshot.size == 0 or template_img.size == 0:
            return False, 0.0
        if template_img.shape[0] > screenshot.shape[0] or template_img.shape[1] > screenshot.shape[1]:
            template = cv2.resize(template_img, (screenshot.shape[1], screenshot.shape[0]))
        else:
            template = template_img
        result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, _ = cv2.minMaxLoc(result)
        del result
        if template is not template_img:
            del template
        return max_val >= threshold, max_val
    except Exception as e:
        print(Fore.RED + f"模板匹配失败: {e}")
        return False, 0.0

# 匹配
def direct_match(region_ratio, template_img, threshold=0.8):
    screenshot = capture_region(region_ratio)
    matched, similarity = match_template(screenshot, template_img, threshold)
    del screenshot
    return matched, similarity

# 点击
def perform_click(click_info):
    x, y = click_info['x'], click_info['y']
    pyautogui.click(x, y)
    delay = click_info.get('delay', 0.3)
    time.sleep(delay)

# 拖动
def perform_drag(drag_info):
    x1, y1 = drag_info['from']['x'], drag_info['from']['y']
    x2, y2 = drag_info['to']['x'], drag_info['to']['y']
    pyautogui.moveTo(x1, y1)
    pyautogui.drag(x2 - x1, y2 - y1, duration=drag_info.get('duration', 0.5), button='left')

# 商店识别单元
def match_single_item(item, template_img, threshold):
    try:
        matched, similarity = direct_match(item['capture_region'], template_img, threshold)
        return item, matched, similarity
    except Exception as e:
        print(Fore.RED + f"匹配编号 {item['name']} 时出错: {e}")
        return item, False, 0.0

# 轮询
def poll_match(region_ratio, template_img, threshold, poll_interval, max_wait, stop_flag):
    start_time = time.monotonic()
    while (time.monotonic() - start_time) < max_wait:
        if stop_flag():
            return False
        matched, _ = direct_match(region_ratio, template_img, threshold)
        if matched:
            return True
        time.sleep(poll_interval)
    return False

# 维稳
def wait_for_Stabilize(region_list, template_img, threshold, poll_interval, max_wait):
    start_time = time.monotonic()
    prev_results = None
    while (time.monotonic() - start_time) < max_wait:
        current_results = [direct_match(reg, template_img, threshold)[0] for reg in region_list]
        if prev_results is not None and current_results == prev_results:
            return True
        prev_results = current_results
        time.sleep(poll_interval)
    return False

# 并行
def parallel_recognize(executor, tasks, template_img, threshold, verbose=True):
    matched = []
    future_to_item = {executor.submit(match_single_item, item, template_img, threshold): item for item in tasks}
    for future in as_completed(future_to_item):
        item, matched_flag, similarity = future.result()
        if verbose:
            if matched_flag:
                print(f"{item['name']}号：{similarity:.4f}/{threshold}，待点击")
            else:
                print(f"{item['name']}号：{similarity:.4f}/{threshold}")
        if matched_flag:
            matched.append(item)
    return matched



# ========== 综合函数 ==========

# 商店维稳并行识别+点击
def shop_stable_parallel_click(executor, tasks, template_M, similarity_threshold):
    print("等待商店稳定...")
    time.sleep(0.2)
    matched_first = parallel_recognize(executor, tasks, template_M, similarity_threshold, verbose=True)

    for item in matched_first:
        print(f"点击 {item['name']} 号坐标")
        perform_click(item['click'])

    pyautogui.moveTo(900, 700)
    time.sleep(0.2)
    matched_second = parallel_recognize(executor, tasks, template_M, similarity_threshold, verbose=False)
    return max(0, len(matched_first) - len(matched_second))

# 备战维稳矫正识别+拖动
def preparation_stable_correct_drag(count_regions, template_L1, template_L2, template_L3,
                                    template_S1, template_Sx, threshold,
                                    current_counter,drag_set_B,
                                    poll_interval, max_wait, stop_flag,sleep):
    print("等待备战区稳定")
    time.sleep(sleep)

    total_score = 0
    for region in count_regions:
        name = region['name']
        if name == "DL" or name == "DR":
            m1, s1 = direct_match(region, template_L1, threshold)
            m2, s2 = direct_match(region, template_L2, threshold)
            m3, s3 = direct_match(region, template_L3, threshold)
            candidates = []
            if m1: candidates.append((1, s1))
            if m2: candidates.append((2, s2))
            if m3: candidates.append((6, s3))
            if candidates:
                best_score = max(candidates, key=lambda x: x[1])[0]
                total_score += best_score
        elif name == "U":
            m_s1, _ = direct_match(region, template_S1, threshold)
            m_sx, _ = direct_match(region, template_Sx, threshold)
            if m_s1 or m_sx:
                total_score += 1
    new_counter = total_score - 1
    if new_counter < 0:
        new_counter = 0

    if new_counter != current_counter:
        print(Fore.RED + f"计数器矫正：{current_counter} -> {new_counter}")
    else:
        print(Fore.GREEN + "计数器无变化")

    delta_net = 0
    if new_counter >= 6:
        dl_region = next((r for r in count_regions if r['name'] == "DL"), None)
        if dl_region:
            matched = poll_match(dl_region, template_L3, threshold, poll_interval, max_wait, stop_flag)
            if matched:
                print(Fore.GREEN + f"计数器达到6，执行拖动后变为 {new_counter}")
                perform_drag(drag_set_B)
                new_counter -= 6
                delta_net = 17
    return new_counter, delta_net

# 结算
def print_run_summary(start_time, start_global_counter, global_counter, total_sec, total_net):
    elapsed_sec = time.monotonic() - start_time
    elapsed_min = round(elapsed_sec / 60.0, 2)
    delta_global = global_counter - start_global_counter
    new_total_sec = total_sec + elapsed_sec
    new_total_net = total_net + delta_global
    save_accumulated(new_total_sec, new_total_net)

    if elapsed_min > 0:
        avg = delta_global / elapsed_min
        print(Back.BLUE + f"\n========== 本轮运行统计 ==========")
        print(Back.BLUE + f"本轮时长: {elapsed_min} 分钟")
        print(Back.BLUE + f"本轮净赚: {delta_global}")
        print(Back.BLUE + f"本轮效率: {avg:.2f} 每分钟")
    else:
        print(Back.RED + f"\n本轮时长不足1分钟，无法计算效率")

    total_min = round(new_total_sec / 60.0, 2)
    if total_min > 0:
        total_avg = new_total_net / total_min
        print(Back.BLUE + f"========== 累计运行统计 ==========")
        print(Back.BLUE + f"累计时长: {total_min} 分钟")
        print(Back.BLUE + f"累计净赚: {new_total_net}")
        print(Back.BLUE + f"累计效率: {total_avg:.2f} 每分钟")
        print(Back.BLUE + f"================================\n")
    else:
        print(Back.RED + f"累计时长不足1分钟，无法计算效率")
    return new_total_sec, new_total_net

# ========== 主程序 ==========
def main():
    global stop_requested
    (click_set_A, template_M, template_L1, template_L2, template_L3,
     template_S1, template_Sx, similarity_threshold, drag_set_B, drag_poll_interval,
     drag_max_wait, count_regions, MAX_ROUNDS) = init_config_and_templates()

    executor = ThreadPoolExecutor(max_workers=5)
    global_counter = load_global_counter()
    total_sec, total_net = load_accumulated()
    start_time = time.monotonic()
    start_global_counter = global_counter
    counter = 0
    round_count = 0
    paused = False

    hotkey_thread = threading.Thread(target=hotkey_listener, daemon=True)
    hotkey_thread.start()

    # 重启
    def restart_script():
        save_global_counter(global_counter)
        nonlocal total_sec, total_net
        keyboard.remove_hotkey(hotkey_stop)
        keyboard.remove_hotkey(hotkey_pause)
        print(Fore.GREEN + f"已达到预设轮次 {MAX_ROUNDS}，即将重启脚本...")
        new_total_sec, new_total_net = print_run_summary(start_time, start_global_counter, global_counter, total_sec, total_net)
        total_sec, total_net = new_total_sec, new_total_net
        time.sleep(5)
        script_abs_path = os.path.abspath(sys.argv[0])
        python_exe = sys.executable
        os.execv(python_exe, [python_exe, script_abs_path] + sys.argv[1:])

    # 初始计数器
    sleep = 0
    new_counter, delta_net = preparation_stable_correct_drag(
                            count_regions, template_L1, template_L2, template_L3,
                            template_S1, template_Sx, similarity_threshold, counter,drag_set_B,
                            drag_poll_interval, drag_max_wait,lambda: stop_requested,sleep)
    counter = new_counter
    global_counter += delta_net

    say_hello()

    print("开始主循环...")
    time.sleep(1)
    try:
        while not stop_requested:
           # 暂停
            while not command_queue.empty():
                cmd = command_queue.get()
                if cmd == 'pause':
                    paused = not paused
                    print(f"\n{'⏸️ 暂停' if paused else '▶️ 继续'}")
                elif cmd == 'stop':
                    stop_script()
                
            while paused and not stop_requested:
                # 仍然检查命令队列
                while not command_queue.empty():
                    cmd = command_queue.get()
                    if cmd == 'pause':
                        paused = False
                        print("\n▶️ 继续")
                    elif cmd == 'stop':
                        stop_script()
                time.sleep(0.1)

            round_count += 1
            if round_count >= MAX_ROUNDS:
                print(Fore.GREEN + f"已达到预设轮次 {MAX_ROUNDS}")
                restart_script()
            print(Back.BLUE + f"\n=====执行新一轮（{round_count}/{MAX_ROUNDS}）=====")

            # 购买
            tasks = [item for item in click_set_A if item['name'] != "0"]
            clicked_count = shop_stable_parallel_click(executor, tasks, template_M, similarity_threshold)
            if clicked_count > 0:
                print(Fore.GREEN + f"本次成功点击 {clicked_count} 张卡")
                counter += clicked_count
                global_counter -= clicked_count * 2
                print(Back.BLUE + f"当前净赚{global_counter},当前计数器: {counter}")
            else:
                print(Fore.YELLOW + "本次无有效购买")

            # 检查
            if clicked_count == 0 or counter >= 6:
                if clicked_count == 0 :
                    sleep = 0
                else:
                    sleep = 1.7
                    if clicked_count >= 4:
                        sleep = 2.2
                new_counter, delta_net = preparation_stable_correct_drag(
                                        count_regions, template_L1, template_L2, template_L3,
                                        template_S1, template_Sx, similarity_threshold,counter,drag_set_B,
                                        drag_poll_interval, drag_max_wait,lambda: stop_requested,sleep)
                counter = new_counter
                global_counter += delta_net
                if delta_net != 0:
                    continue
                else:
                    print(Fore.YELLOW + "无拖动")

            # 点击1号刷新商店
            item_1 = next((item for item in click_set_A if item['name'] == "0"), None)
            if item_1:
                print(Fore.GREEN + "  点击1号刷新商店")
                perform_click(item_1['click'])
                global_counter -= 1
                save_global_counter(global_counter)
        
                print(Back.BLUE + f"当前净赚{global_counter}")

            time.sleep(0.01)

    except KeyboardInterrupt:
        print("\n收到手动中断，正在退出...")
    finally:
        executor.shutdown(wait=True)
        keyboard.remove_hotkey(hotkey_stop)
        print(Fore.GREEN + "脚本已停止")
        print_run_summary(start_time, start_global_counter, global_counter, total_sec, total_net)
        save_global_counter(0)
        save_accumulated(0, 0)
        print(Back.GREEN + "已重置")
        time.sleep(1000000)



if __name__ == "__main__":
    main()
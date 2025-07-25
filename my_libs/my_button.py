import time
from machine import Pin, FPIOA

class Button:
    """
    改进版按键类，自动处理FPIOA设置和按键消抖
    
    参数:
        pin: 按键连接的GPIO引脚号
        mode: 按键触发模式 ("LOW" 或 "HIGH")
        fpioa_function: FPIOA功能号（默认为GPIO功能）
        debounce_delay: 消抖时间(毫秒)，默认20ms
    """

    def __init__(self, pin, fpioa_function, mode="LOW", debounce_delay=20):
        # 初始化FPIOA
        self.fpioa = FPIOA()
        
        # 设置FPIOA功能映射
        if fpioa_function is not None:
            self.fpioa.set_function(pin, fpioa_function)
        else:
            print("Warning: No FPIOA function set, using GPIO mode only")
        
        # 设置引脚模式
        if mode == "LOW":
            pin_mode = Pin.PULL_UP
        elif mode == "HIGH":
            pin_mode = Pin.PULL_DOWN
        else:
            raise ValueError("Invalid mode. Must be 'LOW' or 'HIGH'")
        
        # 初始化引脚
        self.pin = Pin(pin, Pin.IN, pin_mode)
        self.mode = mode
        
        # 设置按键状态常量
        if mode == "HIGH":  # 高电平有效
            self.BUTTON_PUSHED = 1
            self.BUTTON_UNPUSHED = 0
        elif mode == "LOW":  # 低电平有效
            self.BUTTON_PUSHED = 0
            self.BUTTON_UNPUSHED = 1
        
        # 时间参数
        self.debounce_delay = debounce_delay
        
        # 状态变量
        self.last_state = self.BUTTON_UNPUSHED
        self.last_press_time = 0
    
    def read(self):
        """
        读取按键状态，返回True表示检测到按键按下事件
        """
        current_state = self.pin.value()
        current_time = time.ticks_ms()

        # 检测按键释放（状态从1变为0）
        if current_state == self.BUTTON_UNPUSHED and self.last_state == self.BUTTON_PUSHED:
            self.last_state = current_state
            return False
        # 检测按键按下（状态从0变为1）
        if current_state == self.BUTTON_PUSHED and self.last_state == self.BUTTON_UNPUSHED:
            if current_time - self.last_press_time > self.debounce_delay:
                self.last_press_time = current_time
                self.last_state = current_state
                return True

        self.last_state = current_state
        return False
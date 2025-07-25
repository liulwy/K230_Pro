import time, os, sys

from media.sensor import *
from media.display import *
from media.media import *
from machine import Pin
from machine import FPIOA
from machine import UART


class Button:
    """
    按键类，用于处理按键的状态读取和消抖
    """
    def __init__(self, pin, Mode):
        if Mode == "LOW":
            mode = Pin.PULL_UP
        elif Mode == "HIGH":
            mode = Pin.PULL_DOWN
        self.pin = Pin(pin, Pin.IN, mode)
        self.last_state = 0
        self.last_press_time = 0
        self.debounce_delay = 20  # 毫秒

        if Mode == "HIGH": # 高电平有效
            self.BUTTON_PUSHED = 1
            self.BUTTON_UNPUSHED = 0
        elif Mode == "LOW": # 低电平有效
            self.BUTTON_PUSHED = 0
            self.BUTTON_UNPUSHED = 1

    def read(self):
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





# 定义常量
fpioa = FPIOA()
fpioa.set_function(53, FPIOA.GPIO53)
fpioa.set_function(11, FPIOA.UART2_TXD)
fpioa.set_function(12, FPIOA.UART2_RXD)


uart = UART(UART.UART2, baudrate=115200, bits=UART.EIGHTBITS, parity=UART.PARITY_NONE, stop=UART.STOPBITS_ONE)



#---------------------- 按钮初始化 ---------------------
fpioa.set_function(18, FPIOA.GPIO18)
fpioa.set_function(19, FPIOA.GPIO19)
fpioa.set_function(27, FPIOA.GPIO27)
button_intial = Button(18, "LOW")  # 初始化按键，使用低电平触发
button_SendPoints = Button(19, "LOW")  # 向下位机发送坐标的按键，使用低电平触发
button_FindBlackLine = Button(27, "LOW")  # 查找黑色边框的按键，使用低电平触发
#-------------------------------------------------------


Trans_current_time = 0
Trans_last_time = 0


picture_width = 400
picture_height = 240

sensor_id = 2
sensor = None


# 显示模式选择：可以是 "VIRT"、"LCD" 或 "HDMI"
DISPLAY_MODE = "LCD"

#按键模式选择: 高电平触发，低电平触发，可以是 "HIGH", "LOW"
BUTTON_MODE = "LOW"

# 根据模式设置显示宽高
if DISPLAY_MODE == "VIRT":
    # 虚拟显示器模式
    DISPLAY_WIDTH = ALIGN_UP(1920, 16)
    DISPLAY_HEIGHT = 1080
elif DISPLAY_MODE == "LCD":
    # 3.1寸屏幕模式
    DISPLAY_WIDTH = 800
    DISPLAY_HEIGHT = 480
elif DISPLAY_MODE == "HDMI":
    # HDMI扩展板模式
    DISPLAY_WIDTH = 1920
    DISPLAY_HEIGHT = 1080
else:
    raise ValueError("未知的 DISPLAY_MODE，请选择 'VIRT', 'LCD' 或 'HDMI'")


# 创建显示对象
img_show = image.Image(DISPLAY_WIDTH, DISPLAY_HEIGHT, image.RGB565)


'''
全局变量
'''
function_running_num = 1
pencil_points = [[67, 30], [248, 16], [294, 216], [37, 229], [166, 110]]#边框点以及中心复位点,0-4为边框点，第5个点为复位中心点
black_corners_points = [[0, 0], [0, 0], [0, 0], [0, 0]] #黑色边框点


laser_threhold = [(38, 100, 23, 127, -45, 127)]
laser_threhold_inblack = [(4, 100, 30, 127, -40, 127), (4, 100, 9, 127, -92, 127)]
high_power_laser_threhold = [(63, 100, 0, 8, -75, 59)]
threhold_Main = laser_threhold#当前使用的阈值

# 读对应按键状态
def Read_Button(button):
    return button.read()


def Key_Num():
    global button_intial, button_SendPoints
    if Read_Button(button_intial):
        return 1
    elif Read_Button(button_SendPoints):
        return 2
    return 0



'''
此函数用于初始校准
'''
def machine_init(sensor):
    global pencil_points
    pencil_points = []
    #sensor.stop()
    sensor.reset()

    loop = True
    sensor.run()
    while loop:
        img = sensor.snapshot()

        blobs = img.find_blobs(high_power_laser_threhold, pixels_threshold=10, margin=True)
        if blobs:
            img.draw_cross(blobs[0].cx(), blobs[0].cy(), color=(100,0,255), size=7)
            button_isValid = Read_Button(button_intial)  # 读取校准按键状态
            if button_isValid:
                if len(pencil_points) < 5:
                    point_cx = blobs[0].cx()
                    point_cy = blobs[0].cy()
                    # 如果pencil_points小于5个点，则添加当前blob的中心点
                    pencil_points.append([blobs[0].cx(), blobs[0].cy()])
                    print("IP POINT FOUND: {},{}".format(point_cx, point_cy))

                    time.sleep_ms(200)
                else:
                    loop = False  # 如果已经有5个点了，则退出循环
        for n in range(len(pencil_points)):
            img.draw_cross(pencil_points[n][0],pencil_points[n][1],color=(0,0,255))
            #img.draw_string(pencil_points[n][0],pencil_points[n][1],str(n),color=(0,0,255))

        #img.compressed_for_ide(50)
        img_show.clear()
        img_show.draw_image(img, 0, 0, DISPLAY_WIDTH/img.width(), DISPLAY_HEIGHT/img.height())
        Display.show_image(img_show)



def UART_Receive():
    info = uart.read()
    if info:
        info = info.decode('utf-8').strip()
        if info == "reset":
            uart.write("CP:{},{}".format(pencil_points[4][0], pencil_points[4][1]))  # 发送复位中心点
        return info
    return None

'''
此函数用于查找白纸上的激光点
同时会将找到的点每100ms通过串口发送出去
'''
def find_points(sensor, threshold_t):
    global Trans_current_time, Trans_last_time, function_running_num, threhold_Main
    while function_running_num == 2:
        img = sensor.snapshot()
        Trans_current_time = time.ticks_ms()
        blobs = img.find_blobs(threshold_t, pixels_threshold=8, margin=True)
        if blobs:
            point_cx = blobs[0].cx()
            point_cy = blobs[0].cy()
            #print("find point in {},{}".format(point_cx, point_cy))
            img.draw_cross(blobs[0].cx(),blobs[0].cy(),color=(0,100,255), size=7)
            if Trans_current_time - Trans_last_time > 60:
                uart.write("RP:{},{}\r\n".format(point_cx, point_cy))
                #print("Send point: {},{}".format(point_cx, point_cy))
                Trans_last_time = Trans_current_time
        #img.compressed_for_ide()

        flag_send = Read_Button(button_SendPoints)
        if flag_send:
            for i,point in enumerate(pencil_points):
                str = "IP:{},{}\r\n".format(point[0],point[1])
                uart.write(str)
                time.sleep_ms(100)
                #print(str)

        if Read_Button(button_FindBlackLine):
            print("Find Black Line button pressed")
            function_running_num = 3
            return

        if Read_Button(button_intial):
            threhold_Main = laser_threhold
            return
            
            

        img_show.clear()
        img_show.draw_image(img, 0, 0, DISPLAY_WIDTH/img.width(), DISPLAY_HEIGHT/img.height())
        Display.show_image(img_show)



def my_findlines(img):
    lines = img.find_line_segments(merge_distance=20, max_theta_diff=10)
    count = 0  # 初始化线段计数器

    print("------线段统计开始------")
    for line in lines:
        img.draw_line(line.line(), color=(1, 147, 230), thickness=3)  # 绘制线段
        print(f"Line {count}: {line}")  # 打印线段信息
        count += 1  # 更新计数器
    print("---------END---------")




def detect_black_line(sensor):
    global black_corners_points
    black_corners_points = []
    sensor.reset()
    #sensor.set_contrast(3)

    found = False

    sensor.run()
    while not found:
        max_rect = None
        max_rect_area = 0
        img = sensor.snapshot()
        #img = img.copy(roi=(50,16,100,108))
        #img.midpoint(1, bias=0.9, threshold=True, offset=5, invert=True)
        img_rect = img.to_grayscale(copy=True)
        img_rect = img_rect.binary([(91, 221)])

        rr = img_rect.find_rects(threshold=10000) #小于threshold的矩形将被过滤
        if rr:
            max_rect = None
            max_rect_area = 0

            for i, ret in enumerate(rr):
                # 只保留最大矩形
                if max_rect is None or ret.magnitude() > max_rect_area:
                    max_rect = ret
                    max_rect_area = ret.magnitude()

            if max_rect:  # 确保找到了矩形
                corners = max_rect.corners()

                # 清空并重新填充角点列表
                black_corners_points.clear()
                for p in corners:
                    black_corners_points.append([p[0], p[1]])

                # 绘制矩形边界
                for i in range(4):
                    start = corners[i]
                    end = corners[(i + 1) % 4]
                    img.draw_line(start[0], start[1], end[0], end[1], color=(15, 255, 15), thickness=1)

                # 标记角点
                for p in corners:
                    img.draw_circle(p[0], p[1], 5, color=(0, 255, 15))

                found = True
        #img.compressed_for_ide()
        img_show.clear()
        img_show.draw_image(img, 0, 0, DISPLAY_WIDTH/img.width(), DISPLAY_HEIGHT/img.height())
        Display.show_image(img_show)



try:
    # 构造一个具有默认配置的摄像头对象
    sensor = Sensor(id=sensor_id)
    # 重置摄像头sensor
    sensor.reset()


    # 设置通道0的输出尺寸为1920x1080
    sensor.set_framesize(width=picture_width, height=picture_height, chn=CAM_CHN_ID_0)
    #sensor.set_framesize(width=1024, height=768)
    # 设置通道0的输出像素格式为RGB565
    sensor.set_pixformat(Sensor.RGB565, chn=CAM_CHN_ID_0)

    # 根据模式初始化显示器
    if DISPLAY_MODE == "VIRT":
        Display.init(Display.VIRT, width=DISPLAY_WIDTH, height=DISPLAY_HEIGHT, fps=60)
    elif DISPLAY_MODE == "LCD":
        Display.init(Display.ST7701, width=DISPLAY_WIDTH, height=DISPLAY_HEIGHT, to_ide=True)
    elif DISPLAY_MODE == "HDMI":
        Display.init(Display.LT9611, width=DISPLAY_WIDTH, height=DISPLAY_HEIGHT, to_ide=True)

    # 初始化媒体管理器
    MediaManager.init()
    # 启动传感器
    sensor.run()



    # 主循环
    while True:
        os.exitpoint()
        # 显示捕获的图像，中心对齐，居中显示
#        detect_black_line(sensor)



        if function_running_num == 1:
            threhold_Main = laser_threhold
            machine_init(sensor)
            function_running_num = 2
            for i,point in enumerate(pencil_points):
                str = "IP:{},{}\r\n".format(point[0],point[1])
                uart.write(str)
                time.sleep_ms(100)
                print(str)
        elif function_running_num == 2:
            find_points(sensor, threhold_Main)
        elif function_running_num == 3:
            print("into black")
            detect_black_line(sensor)
            print("返回激光点程序并发送角点坐标")
            for i, point in enumerate(black_corners_points):
                str = "BP:{},{}\r\n".format(point[0],point[1])
                uart.write(str)
                time.sleep_ms(100)
                print(str)
            threhold_Main = laser_threhold_inblack
            function_running_num = 2#返回到寻找激光点




except KeyboardInterrupt as e:
    print("用户停止: ", e)
except BaseException as e:
    print(f"异常: {e}")
finally:
    # 停止传感器运行
    if isinstance(sensor, Sensor):
        sensor.stop()
    # 反初始化显示模块
    Display.deinit()
    os.exitpoint(os.EXITPOINT_ENABLE_SLEEP)
    time.sleep_ms(100)
    # 释放媒体缓冲区
    MediaManager.deinit()

import os
import time
import cv_lite
from media.sensor import *
from media.display import *
from media.media import *
from machine import FPIOA, Pin, TOUCH
import gc
from my_libs.my_button import Button

# 颜色配置
COLORS = [
    (255, 0, 0),    # 红色
    (0, 255, 0),    # 绿色
    (0, 0, 255),    # 蓝色
    (255, 255, 0),  # 黄色
    (255, 0, 255),  # 紫色
    (0, 255, 255),  # 青色
    (255, 128, 0),  # 橙色
    (128, 0, 255),  # 紫罗兰
]

# 模式定义
Mode_Flag = 0
Mode_lst = ['正常显示', 'CV_Lite色块检测']

# CV_Lite参数配置
threshold = [120, 255, 0, 50, 0, 50]  # LAB阈值 [L_min, L_max, A_min, A_max, B_min, B_max]
min_area = 100    # 最小色块面积
kernel_size = 1   # 腐蚀膨胀核大小

# 触摸初始化
tp = TOUCH(0)
touch_counter = 0

# 显示配置
display_mode = "lcd"
if display_mode == "lcd":
    DISPLAY_WIDTH = ALIGN_UP(800, 16)
    DISPLAY_HEIGHT = 480
else:
    DISPLAY_WIDTH = ALIGN_UP(1920, 16)
    DISPLAY_HEIGHT = 1080

# 图像尺寸配置 [高, 宽] - cv_lite要求的格式
image_shape = [480, 640]

# 按钮初始化
Mode_Change_button = Button(18, FPIOA.GPIO18, "LOW")
Param_Adjust_button = Button(19, FPIOA.GPIO19, "LOW")  # 参数调整按钮

def Show_Img_2_Screen(img, x=0, y=0):
    """将图像显示到屏幕上，支持缩放 - 参照Contry_Dian_Template.py"""
    img_show = image.Image(DISPLAY_WIDTH, DISPLAY_HEIGHT, image.RGB565)
    img_show.clear()
    img_show.draw_image(img, x, y, DISPLAY_WIDTH/img.width(), DISPLAY_HEIGHT/img.height())
    Display.show_image(img_show, 0, 0)

def cvlite_detection_mode(sensor):
    """CV_Lite色块检测模式"""
    global threshold, min_area, kernel_size
    
    print("进入CV_Lite色块检测模式")
    print(f"当前参数: 阈值{threshold}, 最小面积{min_area}, 核大小{kernel_size}")
    
    while Mode_Flag == 1:
        # 获取摄像头图像
        cam_img = sensor.snapshot(chn=CAM_CHN_ID_0)
        if cam_img is None:
            continue

        # 转换为RGB888格式并获取numpy引用
        if cam_img.format() != image.RGB888:
            cam_img = cam_img.to_rgb888()
        
        img_np = cam_img.to_numpy_ref()

        try:
            # 使用cv_lite进行色块检测
            blobs = cv_lite.rgb888_find_blobs(image_shape, img_np, threshold, min_area, kernel_size)
            
            print(f"检测到 {len(blobs)} 个色块")
            
            # 在原图上绘制检测结果
            for i, blob in enumerate(blobs):
                if len(blob) >= 4:  # 确保有足够的数据 [x, y, w, h, ...]
                    x, y, w, h = blob[:4]
                    color = COLORS[i % len(COLORS)]
                    
                    # 绘制边界框
                    cam_img.draw_rectangle(x, y, w, h, color=color, thickness=3)
                    
                    # 绘制中心点
                    center_x = x + w // 2
                    center_y = y + h // 2
                    cam_img.draw_cross(center_x, center_y, 8, color=color, thickness=3)
                    
                    # 显示编号和坐标信息
                    info_text = f"#{i+1} ({center_x},{center_y})"
                    cam_img.draw_string_advanced(x, max(20, y-25), 20, info_text, color=color)
                    
                    # 显示面积信息（如果有的话）
                    if len(blob) >= 5:
                        area_text = f"面积:{blob[4]}"
                        cam_img.draw_string_advanced(x, max(40, y-5), 16, area_text, color=color)
                    else:
                        # 计算面积
                        area = w * h
                        area_text = f"面积:{area}"
                        cam_img.draw_string_advanced(x, max(40, y-5), 16, area_text, color=color)

            # 在图像上显示检测参数信息
            param_text = f"CV_Lite: [{','.join(map(str,threshold))}] 面积>={min_area} 核={kernel_size}"
            cam_img.draw_rectangle(10, 10, 620, 25, color=(0, 0, 0), thickness=2, fill=True)
            cam_img.draw_string_advanced(15, 12, 16, param_text, color=(255, 255, 255))
            
            # 显示检测统计
            stats_text = f"检测到 {len(blobs)} 个色块"
            cam_img.draw_rectangle(10, 40, 200, 25, color=(0, 0, 0), thickness=2, fill=True)
            cam_img.draw_string_advanced(15, 42, 18, stats_text, color=(255, 255, 255))

        except Exception as e:
            print(f"CV_Lite检测错误: {e}")
            # 显示错误信息
            cam_img.draw_rectangle(10, 10, 300, 25, color=(255, 0, 0), thickness=2, fill=True)
            cam_img.draw_string_advanced(15, 12, 16, f"检测错误: {str(e)[:20]}", color=(255, 255, 255))

        # 使用Show_Img_2_Screen显示图像
        Show_Img_2_Screen(cam_img)

        # 检查参数调整按钮 - 循环调整参数
        if Param_Adjust_button.read():
            # 简单的参数循环调整
            if min_area == 100:
                min_area = 200
                print(f"最小面积调整为: {min_area}")
            elif min_area == 200:
                min_area = 50
                print(f"最小面积调整为: {min_area}")
            else:
                min_area = 100
                print(f"最小面积调整为: {min_area}")
            time.sleep_ms(300)  # 防抖延时

        # 检查模式切换
        if Mode_Change_button.read():
            Mode_Flag = (Mode_Flag + 1) % len(Mode_lst)
            print(f"切换到模式: {Mode_lst[Mode_Flag]}")
            time.sleep_ms(300)
            break

        time.sleep_ms(50)

try:
    # 初始化传感器
    sensor = Sensor()
    sensor.reset()
    sensor.set_hmirror(False)
    sensor.set_vflip(False)

    # 设置摄像头 - 与image_shape匹配
    sensor.set_framesize(width=640, height=480, chn=CAM_CHN_ID_0)
    sensor.set_pixformat(Sensor.RGB565, chn=CAM_CHN_ID_0)

    # 初始化显示
    if display_mode == "lcd":
        Display.init(Display.ST7701, to_ide=True)
    else:
        Display.init(Display.LT9611, to_ide=True)

    print("使用非绑定显示模式")
    print("初始化CV_Lite色块检测测试")
    print(f"图像尺寸: {image_shape} (高x宽)")
    print(f"初始参数: 阈值{threshold}, 最小面积{min_area}, 核大小{kernel_size}")

    # 初始化媒体
    MediaManager.init()
    sensor.run()

    # 主循环
    while True:
        # 处理模式切换按钮
        if Mode_Change_button.read():
            Mode_Flag = (Mode_Flag + 1) % len(Mode_lst)
            print(f"切换到模式: {Mode_lst[Mode_Flag]}")
            time.sleep_ms(300)

        # 处理不同模式
        if Mode_Flag == 0:  # 正常显示模式
            cam_img = sensor.snapshot(chn=CAM_CHN_ID_0)
            if cam_img is not None:
                # 显示实时摄像头画面，并显示当前参数
                if cam_img.format() != image.RGB888:
                    cam_img = cam_img.to_rgb888()
                
                # 在图像上显示当前参数
                param_text = f"正常模式 - 参数: [{','.join(map(str,threshold))}] 面积>={min_area} 核={kernel_size}"
                cam_img.draw_rectangle(10, 10, 620, 25, color=(0, 100, 0), thickness=2, fill=True)
                cam_img.draw_string_advanced(15, 12, 16, param_text, color=(255, 255, 255))
                
                # 显示操作提示
                help_text = "按钮18: 切换模式  按钮19: 调整参数"
                cam_img.draw_rectangle(10, 40, 400, 20, color=(0, 0, 100), thickness=2, fill=True)
                cam_img.draw_string_advanced(15, 42, 14, help_text, color=(255, 255, 255))
                
                Show_Img_2_Screen(cam_img)

        elif Mode_Flag == 1:  # CV_Lite色块检测模式
            cvlite_detection_mode(sensor)

        # 在正常模式下也可以调整参数
        if Mode_Flag == 0 and Param_Adjust_button.read():
            # 循环调整最小面积参数
            if min_area == 100:
                min_area = 200
            elif min_area == 200:
                min_area = 50
            else:
                min_area = 100
            print(f"参数调整: 最小面积 = {min_area}")
            time.sleep_ms(300)

        time.sleep_ms(10)

except KeyboardInterrupt as e:
    print("用户停止: ", e)
except BaseException as e:
    print(f"异常: {e}")
finally:
    if isinstance(sensor, Sensor):
        sensor.stop()
    Display.deinit()
    MediaManager.deinit()
    print("清理完成")
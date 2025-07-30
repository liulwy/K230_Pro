import os
import time
from media.sensor import *
from media.display import *
from media.media import *
from machine import FPIOA, Pin, TOUCH
import gc
import my_libs.detect_obj
from my_libs.detect_obj import ObjectDetector
from my_libs.my_button import Button



# 颜色盘
color_four = [(255, 220, 20, 60), (255, 119, 11, 32), (255, 0, 0, 142), (255, 0, 0, 230),
        (255, 106, 0, 228), (255, 0, 60, 100), (255, 0, 80, 100), (255, 0, 0, 70),
        (255, 0, 0, 192), (255, 250, 170, 30), (255, 100, 170, 30), (255, 220, 220, 0),
        (255, 175, 116, 175), (255, 250, 0, 30), (255, 165, 42, 42), (255, 255, 77, 255),
        (255, 0, 226, 252), (255, 182, 182, 255), (255, 0, 82, 0), (255, 120, 166, 157),
        (255, 110, 76, 0), (255, 174, 57, 255), (255, 199, 100, 0), (255, 72, 0, 118),
        (255, 255, 179, 240), (255, 0, 125, 92), (255, 209, 0, 151), (255, 188, 208, 182),
        (255, 0, 220, 176), (255, 255, 99, 164), (255, 92, 0, 73), (255, 133, 129, 255),
        (255, 78, 180, 255), (255, 0, 228, 0), (255, 174, 255, 243), (255, 45, 89, 255),
        (255, 134, 134, 103), (255, 145, 148, 174), (255, 255, 208, 186),
        (255, 197, 226, 255), (255, 171, 134, 1), (255, 109, 63, 54), (255, 207, 138, 255),
        (255, 151, 0, 95), (255, 9, 80, 61), (255, 84, 105, 51), (255, 74, 65, 105),
        (255, 166, 196, 102), (255, 208, 195, 210), (255, 255, 109, 65), (255, 0, 143, 149),
        (255, 179, 0, 194), (255, 209, 99, 106), (255, 5, 121, 0), (255, 227, 255, 205),
        (255, 147, 186, 208), (255, 153, 69, 1), (255, 3, 95, 161), (255, 163, 255, 0),
        (255, 119, 0, 170), (255, 0, 182, 199), (255, 0, 165, 120), (255, 183, 130, 88),
        (255, 95, 32, 0), (255, 130, 114, 135), (255, 110, 129, 133), (255, 166, 74, 118),
        (255, 219, 142, 185), (255, 79, 210, 114), (255, 178, 90, 62), (255, 65, 70, 15),
        (255, 127, 167, 115), (255, 59, 105, 106), (255, 142, 108, 45), (255, 196, 172, 0),
        (255, 95, 54, 80), (255, 128, 76, 255), (255, 201, 57, 1), (255, 246, 0, 122),
        (255, 191, 162, 208)]

# 模式定义
Mode_Flag = 0
Mode_lst = ['normal', 'Threshold_Adjustment', 'Find_Purple_Point', 'Find_Rects']

# 初始阈值
threshold_dict = {
    'rect': [[11, 39]],
    'purple_point': []
}

# 题目点字典
Points_Dict = {
    'pencil_rect': [],# 最后一点为矩形中心点
    'black_rect': []
}

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

OUT_RGB888P_WIDTH = ALIGN_UP(1080, 16)
OUT_RGB888P_HEIGH = 720

# 裁剪图像的ROI，格式为(x, y, w, h)
cut_roi = (600, 360, 360, 360)

# 按钮初始化
Mode_Change_button = Button(18, FPIOA.GPIO18, "LOW")  # 模式切换按钮
Click_Button = Button(19, FPIOA.GPIO19, "LOW")  # 点击按钮


def witch_key(x, y):
    """判断按下的按钮是哪一个，恢复样例代码的按钮判断逻辑"""
    if x < 160:  # 恢复原来的按钮宽度
        if y < 40:
            return "return"
        if y > 480 - 40:
            return "reset"
        if not y > 60:  # 恢复原来的开始位置
            return None
        if (y - 60) % 60 < 40:  # 恢复原来的间隔和高度
            return str((y - 60) // 60)
    elif x > 800 - 160:  # 恢复原来的按钮宽度
        if y < 40:
            return "change"
        if y > 480 - 40:
            return "save"
        if not y > 60:  # 恢复原来的开始位置
            return None
        if (y - 60) % 60 < 40:  # 恢复原来的间隔和高度
            return str((y - 60) // 60 + 6)
    return None

def threshold_adjustment_mode(sensor):
    """阈值调整模式"""
    global Mode_Flag, threshold_dict

    print("进入阈值调整模式")
    print("准备显示阈值调整界面")

    # 清空当前的阈值
    for key in threshold_dict.keys():
        threshold_dict[key] = []

    button_color = (150, 150, 150)
    text_color = (0, 0, 0)

    # 可以调多个阈值
    threshold_mode_lst = list(threshold_dict.keys())
    threshold_mode_idx = 0
    threshold_mode = threshold_mode_lst[threshold_mode_idx]
    # 初始阈值：L通道[0,100]，A/B通道[0,255]
    threshold_current = [0, 100, 0, 255, 0, 255]  # L_min, L_max, A_min, A_max, B_min, B_max

    # 添加按钮防抖变量
    last_button_time = 0
    button_debounce_delay = 300  # 300ms防抖延时，用于功能按钮
    slider_debounce_delay = 120  # 100ms防抖延时，用于滑块调整

    while Mode_Flag == 1:  # 阈值调整模式
        # 在每次循环开始时重新创建干净的UI画布，避免残留痕迹
        ui_img = image.Image(800, 480, image.RGB565)
        ui_img.draw_rectangle(0, 0, 800, 480, color=(255, 255, 255), thickness=2, fill=True)

        # 重新绘制所有固定的UI元素
        # 按钮--返回
        ui_img.draw_rectangle(0, 0, 160, 40, color=button_color, thickness=2, fill=True)
        ui_img.draw_string_advanced(50, 0, 30, "返回", color=text_color)

        # 按钮--切换
        ui_img.draw_rectangle(800-160, 0, 160, 40, color=button_color, thickness=2, fill=True)
        ui_img.draw_string_advanced(800-160+50, 0, 30, "切换", color=text_color)

        # 按钮--归位
        ui_img.draw_rectangle(0, 480-40, 160, 40, color=button_color, thickness=2, fill=True)
        ui_img.draw_string_advanced(50, 480-40, 30, "归位", color=text_color)

        # 按钮--保存
        ui_img.draw_rectangle(800-160, 480-40, 160, 40, color=button_color, thickness=2, fill=True)
        ui_img.draw_string_advanced(800-160+50, 480-40, 30, "保存", color=text_color)

        # 绘制12个滑块按钮
        for j in [0, 800 - 160]:
            for i in range(60, 420, 60):
                ui_img.draw_rectangle(j, i, 160, 40, color=button_color, thickness=2, fill=True)

        # 获取摄像头图像 - 使用RGB888通道，参照样例使用CAM_CHN_ID_0
        cam_img = sensor.snapshot(chn=CAM_CHN_ID_0)
        if cam_img is None:
            time.sleep_ms(10)
            continue

        # 裁剪图像ROI，参照样例
        cam_img_roi = cam_img.copy(roi=cut_roi)

        # 根据当前阈值模式处理图像，完全参照样例代码的处理方式
        try:
            if threshold_mode == 'rect':
                # 参照样例的处理方式
                processed_img = cam_img_roi.to_grayscale()
                processed_img = processed_img.binary([threshold_current[:2]])
                processed_img = processed_img.to_rgb565()

            elif threshold_mode == 'purple_point': # 适用范围 LAB阈值
                # LAB阈值处理：L通道不需要偏移，A/B通道需要-128偏移
                # L通道：直接使用[0,100]范围
                # A/B通道：[0,255] -> [-128,127]
                lab_threshold = [
                    threshold_current[0],  # L_min: 直接使用
                    threshold_current[1],  # L_max: 直接使用
                    threshold_current[2] - 128,  # A_min: -128偏移
                    threshold_current[3] - 128,  # A_max: -128偏移
                    threshold_current[4] - 128,  # B_min: -128偏移
                    threshold_current[5] - 128   # B_max: -128偏移
                ]
                processed_img = cam_img_roi.binary([lab_threshold])
                processed_img = processed_img.to_rgb565()
            else:
                processed_img = cam_img_roi
        except Exception as e:
            print(f"图像处理错误: {e}")
            processed_img = cam_img_roi

        # 参照样例：直接在固定UI画布上绘制处理后的图像，使用样例的中央显示方式
        img_x = (800 - processed_img.width()) // 2
        img_y = (480 - processed_img.height()) // 2

        # 参照样例：直接在中央绘制图像，不需要额外的区域限制
        ui_img.draw_image(processed_img, img_x, img_y)

        # 绘制滑块标签和当前值，按钮内显示标识，按钮外显示数值
        slider_labels = ["L_min", "L_max", "A_min", "A_max", "B_min", "B_max"]
        for i in range(6):
            y_pos = 60 + i * 60  # 恢复原来的位置：从60开始，间隔60

            # 在按钮内显示标识
            ui_img.draw_string_advanced(5, y_pos + 10, 16, f"-{slider_labels[i]}", color=text_color)
            ui_img.draw_string_advanced(800-155, y_pos + 10, 16, f"+{slider_labels[i]}", color=text_color)

            # 在左侧按钮外面显示当前数值
            ui_img.draw_string_advanced(165, y_pos + 10, 16, f"{threshold_current[i]}", color=text_color)

        # 显示当前模式，参照样例放在合适位置
        ui_img.draw_rectangle(170, 40, 300, 24, color=(255, 255, 255), thickness=2, fill=True)
        ui_img.draw_string_advanced(170, 40, 20, f"当前模式: {threshold_mode}", color=text_color)

        # 处理触摸事件，完全参照样例，添加防抖逻辑
        points = tp.read()
        if len(points) > 0:
            current_time = time.ticks_ms()
            # 判断按下了哪个键
            button = witch_key(points[0].x, points[0].y )
            if button:
                # 判断是滑块按钮还是功能按钮，使用不同的防抖延时
                is_slider_button = button.isdigit()  # 数字按钮是滑块按钮
                required_delay = slider_debounce_delay if is_slider_button else button_debounce_delay

                if current_time - last_button_time > required_delay:
                    last_button_time = current_time  # 更新最后按键时间

                    # 如果是返回键
                    if button == "return":
                        Mode_Flag = 0  # 返回正常模式
                        print("退出阈值调整模式")
                        time.sleep_ms(500)  # 参照样例加延时
                        break
                    # 如果是切换键
                    elif button == "change":
                        threshold_mode_idx = (threshold_mode_idx + 1) % len(threshold_mode_lst)
                        threshold_mode = threshold_mode_lst[threshold_mode_idx]
                        # 重置当前阈值：L通道[0,100]，A/B通道[0,255]
                        threshold_current = [0, 100, 0, 255, 0, 255]
                        # 显示切换消息，参照样例的位置和样式
                        ui_img.draw_rectangle(200, 200, 300, 40, color=button_color, thickness=2, fill=True)
                        ui_img.draw_string_advanced(200, 200, 30, f"调整:{threshold_mode}", color=text_color)
                    # 如果是归位键
                    elif button == "reset":
                        threshold_current = [0, 100, 0, 255, 0, 255]  # 重置阈值：L通道[0,100]，A/B通道[0,255]
                        # 显示归位消息，参照样例的位置和样式
                        ui_img.draw_rectangle(200, 200, 300, 40, color=button_color, thickness=2, fill=True)
                        ui_img.draw_string_advanced(200, 200, 30, "滑块归零", color=text_color)
                    # 如果是保存键
                    elif button == "save":
                        # 保存当前阈值，使用正确的LAB转换
                        if threshold_mode == 'rect':
                            threshold_dict[threshold_mode].append(threshold_current[:2])
                        elif threshold_mode == 'red_point' or threshold_mode == 'red_point_inblack':
                            # LAB阈值转换：L通道直接使用，A/B通道减128
                            saved_threshold = [
                                threshold_current[0],  # L_min: 直接使用
                                threshold_current[1],  # L_max: 直接使用
                                threshold_current[2] - 128,  # A_min: -128偏移
                                threshold_current[3] - 128,  # A_max: -128偏移
                                threshold_current[4] - 128,  # B_min: -128偏移
                                threshold_current[5] - 128   # B_max: -128偏移
                            ]
                            threshold_dict[threshold_mode].append(saved_threshold)
                        print(f"保存阈值: {threshold_dict[threshold_mode]}")
                        # 显示保存成功消息，参照样例的位置和样式
                        ui_img.draw_rectangle(200, 200, 300, 40, color=button_color, thickness=2, fill=True)
                        ui_img.draw_string_advanced(200, 200, 30, "保存成功", color=text_color)
                    else:
                        # 调整阈值滑块，根据通道类型设置不同的范围
                        button_idx = int(button)
                        if button_idx >= 6:
                            # 增加阈值，参照样例使用+2的步长
                            channel = button_idx - 6
                            if channel < 2:  # L通道：范围[0,100]
                                threshold_current[channel] = min(100, threshold_current[channel] + 1)
                            else:  # A/B通道：范围[0,255]
                                threshold_current[channel] = min(255, threshold_current[channel] + 1)
                        else:
                            # 减少阈值，参照样例使用-2的步长
                            channel = button_idx
                            threshold_current[channel] = max(0, threshold_current[channel] - 1)

        # 参照样例直接显示UI，不需要额外的缩放处理
        img_show = image.Image(DISPLAY_WIDTH, DISPLAY_HEIGHT, image.RGB565)
        img_show.clear()
        img_show.draw_image(ui_img, 0, 0, DISPLAY_WIDTH/ui_img.width(), DISPLAY_HEIGHT/ui_img.height())
        Display.show_image(img_show, 0, 0)

        time.sleep_ms(50)  # 参照样例的延时



# 显示图像到屏幕上，支持缩放
# 参数: img - 输入图像，x, y - 显示位置
def Show_Img_2_Screen(img, x=0, y=0):
    """将图像显示到屏幕上，支持缩放"""
    img_show = image.Image(DISPLAY_WIDTH, DISPLAY_HEIGHT, image.RGB565)
    img_show.clear()
    img_show.draw_image(img, x, y, DISPLAY_WIDTH/img.width(), DISPLAY_HEIGHT/img.height())
    Display.show_image(img_show, 0, 0)




# 查找点函数
# 该函数用于查找图像中的点，并在找到的点上绘制十字标记
# 参数: image - 输入图像，threshold_used - 阈值
# 返回: 找到的点列表
def My_Find_Point(image, threshold_used):
    blobs = image.find_blobs(threshold_used, pixels_threshold=8, margin=10)
    return blobs



# 查找矩形函数
# 该函数用于查找图像中的黑色矩形，并返回角点坐标和中心点
# 参数: image - 输入图像，threshold_used - 阈值
# 返回: 找到的矩形信息字典，包含角点和中心点
def My_Find_Rect(image, threshold_used):
    """
    查找黑色矩形并返回角点和中心点
    返回格式: {
        'corners': [[x1,y1], [x2,y2], [x3,y3], [x4,y4]],  # 四个角点
        'center': [cx, cy],  # 中心点
        'found': True/False  # 是否找到矩形
    }
    """
    result = {
        'corners': [],
        'center': [0, 0],
        'found': False
    }

    try:
        # 转换为灰度图像
        img_rect = image.to_grayscale(copy=True)

        # 应用阈值，找到黑色区域
        img_rect = img_rect.binary(threshold_used)

        # 查找矩形，参考23年代码的参数设置
        rects = img_rect.find_rects(threshold=30000)  # 小于threshold的矩形将被过滤

        if rects:
            # 找到面积最大的矩形
            max_rect = None
            max_rect_area = 0

            for rect in rects:
                if max_rect is None or rect.magnitude() > max_rect_area:
                    max_rect = rect
                    max_rect_area = rect.magnitude()

            if max_rect:
                # 获取角点
                corners = max_rect.corners()
                result['corners'] = [[p[0], p[1]] for p in corners]

                # 计算中心点
                center_x = sum(p[0] for p in corners) // 4
                center_y = sum(p[1] for p in corners) // 4
                result['center'] = [center_x, center_y]
                result['found'] = True

                # 在原图上绘制矩形边界和角点
                for i in range(4):
                    start = corners[i]
                    end = corners[(i + 1) % 4]
                    image.draw_line(start[0], start[1], end[0], end[1],
                                   color=(0, 255, 0), thickness=2)

                # 绘制角点
                for p in corners:
                    image.draw_circle(p[0], p[1], 5, color=(255, 0, 0))

                # 绘制中心点
                image.draw_cross(center_x, center_y, 10, color=(255, 255, 0), thickness=3)

    except Exception as e:
        print(f"矩形检测错误: {e}")

    return result

try:
    # 初始化传感器
    sensor = Sensor()
    sensor.reset()
    sensor.set_hmirror(False)
    sensor.set_vflip(False)

    # 设置视频通道
    sensor.set_framesize(width=800, height=480, chn=CAM_CHN_ID_0)
    # sensor.set_pixformat(PIXEL_FORMAT_YUV_SEMIPLANAR_420, chn=CAM_CHN_ID_0)
    sensor.set_pixformat(Sensor.RGB565, chn=CAM_CHN_ID_0)

    # 设置AI处理通道
    sensor.set_framesize(width=OUT_RGB888P_WIDTH, height=OUT_RGB888P_HEIGH, chn=CAM_CHN_ID_2)
    sensor.set_pixformat(PIXEL_FORMAT_RGB_888_PLANAR, chn=CAM_CHN_ID_2)

    # 绑定显示层 - 尝试非绑定显示方式
    # sensor_bind_info = sensor.bind_info(x=0, y=0, chn=CAM_CHN_ID_0)
    # Display.bind_layer(**sensor_bind_info, layer=Display.LAYER_VIDEO1)

    # 初始化显示
    if display_mode == "lcd":
        Display.init(Display.ST7701, to_ide=True)
    else:
        Display.init(Display.LT9611, to_ide=True)

    # 非绑定模式不需要OSD图层
    # osd_img = image.Image(DISPLAY_WIDTH, DISPLAY_HEIGHT, image.ARGB8888)

#    # 初始化检测器
#    detector = ObjectDetector("/sdcard/mp_deployment_source/deploy_config.json")

    # 初始化媒体
    MediaManager.init()

    # 启动传感器
    sensor.run()

    # 主循环
    while True:
        # 处理模式切换按钮
        if Mode_Change_button.read():
            Mode_Flag = (Mode_Flag + 1) % len(Mode_lst)
            if Mode_Flag == 1:
                Mode_Flag += 1 # 非屏幕长按不进入阈值调整模式
            print(f"切换到模式: {Mode_lst[Mode_Flag]}")
            time.sleep_ms(300)  # 防抖延时

        # 处理不同模式
        if Mode_Flag == 0:  # 正常模式
            # 非绑定显示模式：手动获取并显示摄像头图像
            cam_img = sensor.snapshot(chn=CAM_CHN_ID_0)
            if cam_img is not None:
                # 创建显示图像
                display_img = image.Image(DISPLAY_WIDTH, DISPLAY_HEIGHT, image.RGB565)
                display_img.clear()
                # 将摄像头图像缩放到显示尺寸
                display_img.draw_image(cam_img, 0, 0, DISPLAY_WIDTH/cam_img.width(), DISPLAY_HEIGHT/cam_img.height())
                # 直接显示，不使用层级
                Display.show_image(display_img, 0, 0)

            # 不再需要OSD层的清空操作
            # osd_img.clear()
            # Display.show_image(osd_img, 0, 0, Display.LAYER_OSD3)

        elif Mode_Flag == 1:  # 阈值调整模式
            threshold_adjustment_mode(sensor)

#        elif Mode_Flag == 2:  # 目标检测模式
#            # 获取摄像头图像（用于显示和目标检测）
#            cam_img = sensor.snapshot(chn=CAM_CHN_ID_0)  # 用于显示的YUV图像
#            rgb888p_img = sensor.snapshot(chn=CAM_CHN_ID_2)  # 用于AI检测的RGB图像

#            if cam_img is None or rgb888p_img is None:
#                continue

#            # 进行目标检测
#            detections = detector.get_detection_results(rgb888p_img)

#            # 创建显示图像，将摄像头图像作为背景
#            display_img = image.Image(DISPLAY_WIDTH, DISPLAY_HEIGHT, image.RGB565)
#            display_img.clear()
#            # 绘制摄像头图像作为背景
#            display_img.draw_image(cam_img, 0, 0, DISPLAY_WIDTH/cam_img.width(), DISPLAY_HEIGHT/cam_img.height())

#            # 在显示图像上绘制检测结果
#            for det in detections:
#                # 坐标转换：AI通道尺寸 → 显示尺寸
#                scale_x = DISPLAY_WIDTH / OUT_RGB888P_WIDTH
#                scale_y = DISPLAY_HEIGHT / OUT_RGB888P_HEIGH

#                x1, y1, x2, y2 = det["coordinates"]
#                disp_x1 = int(x1 * scale_x)
#                disp_y1 = int(y1 * scale_y)
#                disp_x2 = int(x2 * scale_x)
#                disp_y2 = int(y2 * scale_y)

#                # 计算宽度和高度
#                w = disp_x2 - disp_x1
#                h = disp_y2 - disp_y1

#                # 获取类别对应的颜色
#                class_id = det["class_id"]
#                color_index = class_id % len(color_four)
#                color = color_four[color_index][1:]  # 取RGB部分，忽略第一个alpha值

#                # 绘制边界框
#                display_img.draw_rectangle(disp_x1, disp_y1, w, h, color=color, thickness=2)

#                # 显示标签和置信度
#                label = det['label']
#                score = det['confidence']
#                label_text = f"{label}: {score:.2f}"

#                # 计算文本位置，确保不会超出屏幕顶部
#                text_y = max(20, disp_y1 - 20)

#                display_img.draw_string_advanced(
#                    disp_x1,     # X坐标
#                    text_y,      # Y坐标
#                    24,          # 字体大小
#                    label_text,  # 文本内容
#                    color=color  # 颜色使用同框的颜色
#                )

#            # 直接显示合成图像，不使用层级
#            Display.show_image(display_img, 0, 0)




        elif Mode_Flag == 2:  # 查找紫色点模式
            # 获取摄像头图像
            cam_img = sensor.snapshot(chn=CAM_CHN_ID_0)
            if cam_img is None:
                continue

            blobs = My_Find_Point(cam_img, threshold_dict['purple_point'])
            if blobs:
                point_cx = blobs[0].cx()  # 获取第一个点的中心X坐标
                point_cy = blobs[0].cy()  # 获取第一个点的中心
                cam_img.draw_cross(point_cx, point_cy, 8, color=(255, 0, 0), thickness=2)
            # 显示摄像头图像
            Show_Img_2_Screen(cam_img)

        elif Mode_Flag == 3:  # 寻找矩形
            # 获取摄像头图像
            cam_img = sensor.snapshot(chn=CAM_CHN_ID_0)
            if cam_img is None:
                continue

            # 查找黑色矩形
            rect_info = My_Find_Rect(cam_img, threshold_dict['rect'])

            # 在图像上绘制矩形
            if rect_info['found']:
                cam_img.draw_rectangle(rect_info['corners'][0][0], rect_info['corners'][0][1],
                                        rect_info['corners'][1][0] - rect_info['corners'][0][0],
                                        rect_info['corners'][1][1] - rect_info['corners'][0][1],
                                        color=(0, 255, 0), thickness=2)
                cam_img.draw_circle(rect_info['center'][0], rect_info['center'][1], 5, color=(255, 0, 0), thickness=2)

            else:
                # 未找到矩形时的提示
                cam_img.draw_string_advanced(10, 10, 20, "No rectangle found", color=(255, 0, 0))

            # 显示摄像头图像
            Show_Img_2_Screen(cam_img)

            # 点击按钮保存矩形信息
            if Click_Button.read():
                if rect_info['found']:
                    print("保存矩形信息:")
                    print(f"角点坐标: {Points_Dict['black_rect'][:-1]}")
                    print(f"中心坐标: {Points_Dict['black_rect'][-1]}")
                    time.sleep_ms(300)  # 防抖延时
                else:
                    print("未检测到矩形，无法保存")


        # 处理触摸屏长按逻辑
        points = tp.read()
        if len(points) > 0:
            touch_counter += 1
            LONG_PRESS_THRESHOLD = 20  # 长按阈值
            if touch_counter > LONG_PRESS_THRESHOLD:
                Mode_Flag = 1  # 切换到阈值调整模式
                touch_counter = 0  # 重置计数器
        else:
            touch_counter = max(0, touch_counter - 1)

        time.sleep_ms(10)  # 短暂延时

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

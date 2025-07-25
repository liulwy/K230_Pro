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
Mode_lst = ['normal', 'Threshold', 'Object Detection']

# 初始阈值
threshold_dict = {
    'rect': [(78, 255)],
    'red_point': [(52, 100, 24, 127, -49, 41)],
    'red_point_inblack': [(52, 100, 24, 127, -49, 41)]
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


def witch_key(x, y):
    """判断按下的按钮是哪一个"""
    if x < 160:
        if y < 40:
            return "return"
        if y > 480 - 40:
            return "reset"
        if not y > 60:
            return None
        if (y - 60) % 60 < 40:
            return str((y - 60) // 60)
    elif x > 800 - 160:
        if y < 40:
            return "change"
        if y > 480 - 40:
            return "save"
        if not y > 60:
            return None
        if (y - 60) % 60 < 40:
            return str((y - 60) // 60 + 6)
    return None

def threshold_adjustment_mode(sensor):
    """阈值调整模式"""
    global Mode_Flag, threshold_dict

    # 清空当前的阈值
    for key in threshold_dict.keys():
        threshold_dict[key] = []

    button_color = (150, 150, 150)
    text_color = (0, 0, 0)

    # 创建一个画布，用来绘制按钮
    ui_img = image.Image(800, 480, image.RGB565)
    ui_img.draw_rectangle(0, 0, 800, 480, color=(255, 255, 255), thickness=2, fill=True)

    # 按钮--返回，编辑完成后返回
    ui_img.draw_rectangle(0, 0, 160, 40, color=button_color, thickness=2, fill=True)
    ui_img.draw_string_advanced(50, 0, 30, "返回", color=text_color)

    # 按钮--切换，切换编辑的阈值对象
    ui_img.draw_rectangle(800-160, 0, 160, 40, color=button_color, thickness=2, fill=True)
    ui_img.draw_string_advanced(800-160+50, 0, 30, "切换", color=text_color)

    # 按钮--归位，滑块归位
    ui_img.draw_rectangle(0, 480-40, 160, 40, color=button_color, thickness=2, fill=True)
    ui_img.draw_string_advanced(50, 480-40, 30, "归位", color=text_color)

    # 按钮--保存，将当前阈值添加到阈值列表中
    ui_img.draw_rectangle(800-160, 480-40, 160, 40, color=button_color, thickness=2, fill=True)
    ui_img.draw_string_advanced(800-160+50, 480-40, 30, "保存", color=text_color)

    # 绘制12个按钮，对应了6个滑块的控制
    for j in [0, 800 - 160]:
        for i in range(60, 420, 60):
            ui_img.draw_rectangle(j, i, 160, 40, color=button_color, thickness=2, fill=True)

    # 可以调多个阈值
    threshold_mode_lst = list(threshold_dict.keys())
    threshold_mode_idx = 0
    threshold_mode = threshold_mode_lst[threshold_mode_idx]
    threshold_current = [0, 255, 0, 255, 0, 255]  # 初始阈值

    while Mode_Flag == 1:  # 阈值调整模式
        # 获取摄像头图像
        cam_img = sensor.snapshot(chn=CAM_CHN_ID_0)
        cam_img = cam_img.copy(roi=cut_roi)

        # 根据当前阈值模式处理图像
        if threshold_mode == 'rect':
            # 转换为灰度图并应用阈值
            gray_img = cam_img.to_grayscale(copy=True)
            bin_img = gray_img.binary([threshold_current[:2]])
            disp_img = bin_img.to_rgb565()
        elif threshold_mode == 'red_point' or threshold_mode == 'red_point_inblack':
            # 应用颜色阈值
            bin_img = cam_img.binary([threshold_current])
            disp_img = bin_img.to_rgb565()

        # 将处理后的图像绘制到UI上
        ui_img.draw_image(disp_img, (800 - disp_img.width()) // 2, (480 - disp_img.height()) // 2)

        # 显示当前调整的阈值模式
        ui_img.draw_string_advanced(300, 20, 30, f"调整: {threshold_mode}", color=text_color)

        # 处理触摸事件
        points = tp.read()
        if len(points) > 0:
            # 判断按下了哪个键
            button = witch_key(points[0].x, points[0].y)
            if button:
                # 如果是返回键
                if button == "return":
                    Mode_Flag = 0  # 返回正常模式
                    break
                # 如果是切换键
                elif button == "change":
                    threshold_mode_idx = (threshold_mode_idx + 1) % len(threshold_mode_lst)
                    threshold_mode = threshold_mode_lst[threshold_mode_idx]
                    # 重置当前阈值
                    threshold_current = [0, 255, 0, 255, 0, 255]
                # 如果是归位键
                elif button == "reset":
                    threshold_current = [0, 255, 0, 255, 0, 255]  # 重置阈值
                # 如果是保存键
                elif button == "save":
                    # 保存当前阈值
                    if threshold_mode == 'rect':
                        threshold_dict[threshold_mode].append(threshold_current[:2])
                    else:
                        threshold_dict[threshold_mode].append(threshold_current)
                    # 显示保存成功消息
                    ui_img.draw_rectangle(300, 400, 200, 40, color=button_color, thickness=2, fill=True)
                    ui_img.draw_string_advanced(300, 400, 30, "保存成功", color=text_color)
                    Display.show_image(ui_img, 0, 0, Display.LAYER_OSD3)
                    time.sleep_ms(1000)
                else:
                    # 调整阈值滑块
                    button_idx = int(button)
                    if button_idx >= 6:
                        # 增加阈值
                        channel = button_idx - 6
                        threshold_current[channel] = min(255, threshold_current[channel] + 5)
                    else:
                        # 减少阈值
                        channel = button_idx
                        threshold_current[channel] = max(0, threshold_current[channel] - 5)

        # 显示UI
        Display.show_image(ui_img, 0, 0, Display.LAYER_OSD3)
        time.sleep_ms(50)


try:
    # 初始化传感器
    sensor = Sensor()
    sensor.reset()
    sensor.set_hmirror(False)
    sensor.set_vflip(False)

    # 设置视频通道
    sensor.set_framesize(width=DISPLAY_WIDTH, height=DISPLAY_HEIGHT, chn=CAM_CHN_ID_0)
    # sensor.set_pixformat(PIXEL_FORMAT_YUV_SEMIPLANAR_420, chn=CAM_CHN_ID_0)
    sensor.set_pixformat(PIXEL_FORMAT_YUV_SEMIPLANAR_420, chn=CAM_CHN_ID_0)

    # 设置AI处理通道
    sensor.set_framesize(width=OUT_RGB888P_WIDTH, height=OUT_RGB888P_HEIGH, chn=CAM_CHN_ID_2)
    sensor.set_pixformat(PIXEL_FORMAT_RGB_888_PLANAR, chn=CAM_CHN_ID_2)

    # 绑定显示层
    sensor_bind_info = sensor.bind_info(x=0, y=0, chn=CAM_CHN_ID_0)
    Display.bind_layer(**sensor_bind_info, layer=Display.LAYER_VIDEO1)

    # 初始化显示
    if display_mode == "lcd":
        Display.init(Display.ST7701, to_ide=True)
    else:
        Display.init(Display.LT9611, to_ide=True)

    # 创建OSD图层
    osd_img = image.Image(DISPLAY_WIDTH, DISPLAY_HEIGHT, image.ARGB8888)

    # 初始化检测器
    detector = ObjectDetector("/sdcard/mp_deployment_source/deploy_config.json")

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
            # 摄像头图像自动显示，无需额外操作
            # 清空OSD图层
            osd_img.clear()
            Display.show_image(osd_img, 0, 0, Display.LAYER_OSD3)

        elif Mode_Flag == 1:  # 阈值调整模式
            threshold_adjustment_mode(sensor)

        elif Mode_Flag == 2:  # 目标检测模式
            # 获取摄像头图像（用于目标检测）
            rgb888p_img = sensor.snapshot(chn=CAM_CHN_ID_2)
            if rgb888p_img is None:
                continue

            # 进行目标检测
            detections = detector.get_detection_results(rgb888p_img)

            # 清空OSD图像
            osd_img.clear()

            for det in detections:
                # 坐标转换：AI通道尺寸 → 显示尺寸
                scale_x = DISPLAY_WIDTH / OUT_RGB888P_WIDTH
                scale_y = DISPLAY_HEIGHT / OUT_RGB888P_HEIGH

                x1, y1, x2, y2 = det["coordinates"]
                disp_x1 = int(x1 * scale_x)
                disp_y1 = int(y1 * scale_y)
                disp_x2 = int(x2 * scale_x)
                disp_y2 = int(y2 * scale_y)

                # 计算宽度和高度
                w = disp_x2 - disp_x1
                h = disp_y2 - disp_y1

                # 获取类别对应的颜色
                class_id = det["class_id"]
                color_index = class_id % len(color_four)
                color = color_four[color_index][1:]  # 取RGB部分，忽略第一个alpha值

                # 在OSD上绘制边界框
                osd_img.draw_rectangle(disp_x1, disp_y1, w, h, color=color, thickness=2)

                # 显示标签和置信度
                label = det['label']
                score = det['confidence']
                label_text = f"{label}: {score:.2f}"

                # 计算文本位置，确保不会超出屏幕顶部
                text_y = max(20, disp_y1 - 20)

                osd_img.draw_string_advanced(
                    disp_x1,     # X坐标
                    text_y,      # Y坐标
                    24,          # 字体大小（调整为24）
                    label_text,  # 文本内容
                    color=color  # 颜色使用同框的颜色
                )

            # 更新OSD图层
            Display.show_image(osd_img, 0, 0, Display.LAYER_OSD3)

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

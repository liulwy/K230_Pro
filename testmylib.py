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
    if x < 80:  # 调整为新的按钮宽度
        if y < 40:
            return "return"
        if y > 480 - 40:
            return "reset"
        if y < 240:  # 调整开始位置
            return None
        if (y - 240) % 40 < 30:  # 调整间隔和高度
            return str((y - 240) // 40)
    elif x > 800 - 80:  # 调整为新的按钮宽度
        if y < 40:
            return "change"
        if y > 480 - 40:
            return "save"
        if y < 240:  # 调整开始位置
            return None
        if (y - 240) % 40 < 30:  # 调整间隔和高度
            return str((y - 240) // 40 + 6)
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

    # 创建一个固定的UI画布，参照样例代码的做法
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

    # 绘制12个滑块按钮，左右各6个，位置更靠下以腾出更多图像显示空间
    for j in [0, 800 - 80]:  # 减小按钮宽度为80
        for i in range(240, 480-40, 40):  # 从240开始，间隔40，为图像留出更多空间
            ui_img.draw_rectangle(j, i, 80, 30, color=button_color, thickness=2, fill=True)

    # 可以调多个阈值
    threshold_mode_lst = list(threshold_dict.keys())
    threshold_mode_idx = 0
    threshold_mode = threshold_mode_lst[threshold_mode_idx]
    threshold_current = [0, 255, 0, 255, 0, 255]  # 初始阈值

    while Mode_Flag == 1:  # 阈值调整模式
        # 获取摄像头图像 - 使用RGB888通道，参照样例使用CAM_CHN_ID_0
        cam_img = sensor.snapshot(chn=CAM_CHN_ID_0)
        if cam_img is None:
            time.sleep_ms(10)
            continue

        # 裁剪图像ROI，参照样例
        cam_img_roi = cam_img.copy(roi=cut_roi)

        # 根据当前阈值模式处理图像，完全参照样例的处理方式
        try:
            if threshold_mode == 'rect':
                # 参照样例的处理方式
                processed_img = cam_img_roi.to_grayscale()
                processed_img = processed_img.binary([threshold_current[:2]])
                processed_img = processed_img.to_rgb565()
            elif threshold_mode == 'red_point' or threshold_mode == 'red_point_inblack':
                # 参照样例的颜色处理方式
                processed_img = cam_img_roi.binary([threshold_current])
                processed_img = processed_img.to_rgb565()
            else:
                processed_img = cam_img_roi
        except Exception as e:
            print(f"图像处理错误: {e}")
            processed_img = cam_img_roi

        # 参照样例：直接在固定UI画布上绘制处理后的图像，使用更大的显示区域
        img_x = (800 - processed_img.width()) // 2
        img_y = 50  # 从顶部50像素开始，为按钮留出空间
        # 限制图像显示区域不超过底部按钮区域
        max_img_height = 240 - 50  # 最大高度到滑块按钮开始位置
        if processed_img.height() > max_img_height:
            # 如果图像太高，需要缩放
            scale = max_img_height / processed_img.height()
            scaled_width = int(processed_img.width() * scale)
            scaled_height = int(processed_img.height() * scale)
            img_x = (800 - scaled_width) // 2
            # 先清空图像显示区域
            ui_img.draw_rectangle(80, 50, 800-160, 240-50, color=(0, 0, 0), thickness=2, fill=True)
            # 缩放并绘制图像
            ui_img.draw_image(processed_img, img_x, img_y, scale, scale)
        else:
            # 先清空图像显示区域
            ui_img.draw_rectangle(80, 50, 800-160, 240-50, color=(0, 0, 0), thickness=2, fill=True)
            # 直接绘制图像
            ui_img.draw_image(processed_img, img_x, img_y)

        # 绘制滑块标签和当前值，放在底部不遮挡图像
        slider_labels = ["L_min", "L_max", "A_min", "A_max", "B_min", "B_max"]
        for i in range(6):
            y_pos = 240 + i * 40  # 从240开始，间隔40
            # 清空并重新绘制左右按钮的标签
            ui_img.draw_rectangle(2, y_pos + 5, 76, 20, color=button_color, thickness=1, fill=True)
            ui_img.draw_rectangle(802-78, y_pos + 5, 76, 20, color=button_color, thickness=1, fill=True)
            
            # 绘制按钮标签
            ui_img.draw_string_advanced(2, y_pos + 5, 16, f"-{slider_labels[i]}", color=text_color)
            ui_img.draw_string_advanced(802-76, y_pos + 5, 16, f"+{slider_labels[i]}", color=text_color)
            
            # 在中间显示当前值，不遮挡图像
            ui_img.draw_rectangle(90, y_pos + 5, 150, 20, color=(255, 255, 255), thickness=1, fill=True)
            ui_img.draw_string_advanced(90, y_pos + 5, 16, f"{slider_labels[i]}: {threshold_current[i]}", color=text_color)

        # 显示当前模式，放在顶部
        ui_img.draw_rectangle(170, 10, 300, 24, color=(255, 255, 255), thickness=2, fill=True)
        ui_img.draw_string_advanced(170, 10, 20, f"当前模式: {threshold_mode}", color=text_color)

        # 处理触摸事件，完全参照样例
        points = tp.read()
        if len(points) > 0:
            # 判断按下了哪个键
            button = witch_key(points[0].x, points[0].y)
            if button:
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
                    # 重置当前阈值
                    threshold_current = [0, 255, 0, 255, 0, 255]
                    # 显示切换消息，参照样例，位置调整到不遮挡图像的区域
                    ui_img.draw_rectangle(300, 450, 200, 25, color=button_color, thickness=2, fill=True)
                    ui_img.draw_string_advanced(305, 452, 20, f"切换到:{threshold_mode}", color=text_color)
                # 如果是归位键
                elif button == "reset":
                    threshold_current = [0, 255, 0, 255, 0, 255]  # 重置阈值
                    # 显示归位消息，参照样例，位置调整
                    ui_img.draw_rectangle(300, 450, 200, 25, color=button_color, thickness=2, fill=True)
                    ui_img.draw_string_advanced(305, 452, 20, "滑块归零", color=text_color)
                # 如果是保存键
                elif button == "save":
                    # 保存当前阈值，参照样例的保存方式
                    if threshold_mode == 'rect':
                        threshold_dict[threshold_mode].append(threshold_current[:2])
                    elif threshold_mode == 'red_point' or threshold_mode == 'red_point_inblack':
                        threshold_dict[threshold_mode].append(threshold_current)
                    # 显示保存成功消息，参照样例，位置调整
                    ui_img.draw_rectangle(300, 450, 200, 25, color=button_color, thickness=2, fill=True)
                    ui_img.draw_string_advanced(305, 452, 20, "保存成功", color=text_color)
                else:
                    # 调整阈值滑块，参照样例的调整方式
                    button_idx = int(button)
                    if button_idx >= 6:
                        # 增加阈值，参照样例使用+2的步长
                        channel = button_idx - 6
                        threshold_current[channel] = min(255, threshold_current[channel] + 2)
                    else:
                        # 减少阈值，参照样例使用-2的步长
                        channel = button_idx
                        threshold_current[channel] = max(0, threshold_current[channel] - 2)

        # 参照样例直接显示UI，不需要额外的缩放处理
        img_show = image.Image(DISPLAY_WIDTH, DISPLAY_HEIGHT, image.RGB565)
        img_show.clear()
        img_show.draw_image(ui_img, 0, 0, DISPLAY_WIDTH/ui_img.width(), DISPLAY_HEIGHT/ui_img.height())
        Display.show_image(img_show, 0, 0)

        time.sleep_ms(50)  # 参照样例的延时


try:
    # 初始化传感器
    sensor = Sensor()
    sensor.reset()
    sensor.set_hmirror(False)
    sensor.set_vflip(False)

    # 设置视频通道
    sensor.set_framesize(width=DISPLAY_WIDTH, height=DISPLAY_HEIGHT, chn=CAM_CHN_ID_0)
    # sensor.set_pixformat(PIXEL_FORMAT_YUV_SEMIPLANAR_420, chn=CAM_CHN_ID_0)
    sensor.set_pixformat(Sensor.RGB565, chn=CAM_CHN_ID_0)

    # 设置AI处理通道
    sensor.set_framesize(width=OUT_RGB888P_WIDTH, height=OUT_RGB888P_HEIGH, chn=CAM_CHN_ID_2)
    sensor.set_pixformat(PIXEL_FORMAT_RGB_888_PLANAR, chn=CAM_CHN_ID_2)

    # 绑定显示层 - 尝试非绑定显示方式
    # sensor_bind_info = sensor.bind_info(x=0, y=0, chn=CAM_CHN_ID_0)
    # Display.bind_layer(**sensor_bind_info, layer=Display.LAYER_VIDEO1)
    print("使用非绑定显示模式")

    # 初始化显示
    if display_mode == "lcd":
        Display.init(Display.ST7701, to_ide=True)
    else:
        Display.init(Display.LT9611, to_ide=True)

    # 非绑定模式不需要OSD图层
    # osd_img = image.Image(DISPLAY_WIDTH, DISPLAY_HEIGHT, image.ARGB8888)

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

        elif Mode_Flag == 2:  # 目标检测模式
            # 获取摄像头图像（用于显示和目标检测）
            cam_img = sensor.snapshot(chn=CAM_CHN_ID_0)  # 用于显示的YUV图像
            rgb888p_img = sensor.snapshot(chn=CAM_CHN_ID_2)  # 用于AI检测的RGB图像

            if cam_img is None or rgb888p_img is None:
                continue

            # 进行目标检测
            detections = detector.get_detection_results(rgb888p_img)

            # 创建显示图像，将摄像头图像作为背景
            display_img = image.Image(DISPLAY_WIDTH, DISPLAY_HEIGHT, image.RGB565)
            display_img.clear()
            # 绘制摄像头图像作为背景
            display_img.draw_image(cam_img, 0, 0, DISPLAY_WIDTH/cam_img.width(), DISPLAY_HEIGHT/cam_img.height())

            # 在显示图像上绘制检测结果
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

                # 绘制边界框
                display_img.draw_rectangle(disp_x1, disp_y1, w, h, color=color, thickness=2)

                # 显示标签和置信度
                label = det['label']
                score = det['confidence']
                label_text = f"{label}: {score:.2f}"

                # 计算文本位置，确保不会超出屏幕顶部
                text_y = max(20, disp_y1 - 20)

                display_img.draw_string_advanced(
                    disp_x1,     # X坐标
                    text_y,      # Y坐标
                    24,          # 字体大小
                    label_text,  # 文本内容
                    color=color  # 颜色使用同框的颜色
                )

            # 直接显示合成图像，不使用层级
            Display.show_image(display_img, 0, 0)

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

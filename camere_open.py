import time, os, sys

import utime
from media.sensor import *
from media.display import *
from media.media import *

#用CSI2接口的摄像头
sensor_id = 2
sensor = None

try:
    # 构造一个具有默认配置的摄像头对象
    sensor = Sensor(id=sensor_id)
    # 重置摄像头sensor
    sensor.reset()

    # 无需进行镜像翻转
    # 设置水平镜像
    # sensor.set_hmirror(False)
    # 设置垂直翻转
    # sensor.set_vflip(False)

    # 设置通道0的输出尺寸为1920x1080
    sensor.set_framesize(Sensor.FHD, chn=CAM_CHN_ID_0)
    # 设置通道0的输出像素格式为RGB888
    sensor.set_pixformat(Sensor.RGB565, chn=CAM_CHN_ID_0)

    # 使用IDE的帧缓冲区作为显示输出
    Display.init(Display.VIRT, width=1920, height=1080, to_ide=True,fps = 60)
    # 初始化媒体管理器
    MediaManager.init()
    # 启动传感器
    sensor.run()

    colour_theshold = [(0, 80, 30, 79, 23, 87)];

    while True:
        os.exitpoint()

        #捕获通道0的图像
        img = sensor.snapshot(chn=CAM_CHN_ID_0)

        blobs = img.find_blobs(colour_theshold,area_threshold = 2000)

        if blobs:
          # 遍历每个检测到的颜色块
            for blob in blobs:
              # 绘制颜色块的外接矩形
              # blob[0:4] 表示颜色块的矩形框 [x, y, w, h]，
                img.draw_rectangle(blob[0:4])

              # 在颜色块的中心绘制一个十字
              # blob[5] 和 blob[6] 分别是颜色块的中心坐标 (cx, cy)
                img.draw_cross(blob[5], blob[6])

              # 在控制台输出颜色块的中心坐标
                print("Blob Center: X={}, Y={}".format(blob[5], blob[6]))

        Display.show_image(img)

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

from libs.PipeLine import PipeLine, ScopedTiming
from libs.YOLO import YOLOv5
import os,sys,gc
import ulab.numpy as np
import image
import time

def Get_Center(res,yolo):
    centers = []
    if res and isinstance(res[0], (list, np.ndarray)):
        for det in res[0]:
            # 提取原始坐标（基于rgb888p_size）
            try:
                if not isinstance(det, (list, np.ndarray)):
                                print(f"无效检测结果: {type(det)}")
                                continue  # 跳过非结构化数据
                if len(det) < 6:
                                print(f"数据长度不足: {len(det)}")
                                continue
                if any(coord < 0 for coord in det[:4]):
                                print(f"坐标异常: {det[:4]}")
                                continue
                x1, y1, x2, y2 = map(lambda x: int(round(x, 0)), det[:4])

                raw_cx = (x1 + x2) // 2
                raw_cy = (y1 + y2) // 2

                disp_cx = raw_cx * yolo.display_size[0] // yolo.rgb888p_size[0]
                disp_cy = raw_cy * yolo.display_size[1] // yolo.rgb888p_size[1]

                class_id = int(det[5])
                label = yolo.labels[class_id]

                # 构建数据结构
                obj_data = {
                    "label": label,
                    "raw": (raw_cx, raw_cy),
                    "disp": (disp_cx, disp_cy)
                }
                centers.append(obj_data)


            except (TypeError, IndexError) as e:
                print(f"处理检测结果时出错: {str(e)}")

    return centers

if __name__=="__main__":
    # 显示模式，默认"hdmi",可以选择"hdmi"和"lcd"
    display_mode="lcd"
    rgb888p_size=[1280,720]
    if display_mode=="hdmi":
        display_size=[1920,1080]
    else:
        display_size=[800,480]
    kmodel_path="/data/Kmodel/fruits_det.kmodel"
    labels = ["apple","banana","orange"]
    confidence_threshold = 0.8
    nms_threshold=0.45
    model_input_size=[320,320]
    # 初始化PipeLine
    pl=PipeLine(rgb888p_size=rgb888p_size,display_size=display_size,display_mode=display_mode)
    pl.create()
    # 初始化YOLOv5实例
    yolo=YOLOv5(task_type="detect",mode="video",kmodel_path=kmodel_path,labels=labels,rgb888p_size=rgb888p_size,model_input_size=model_input_size,display_size=display_size,conf_thresh=confidence_threshold,nms_thresh=nms_threshold,max_boxes_num=50,debug_mode=0)
    yolo.config_preprocess()
    try:
        last_time = time.ticks_ms()
        while True:
            os.exitpoint()
            with ScopedTiming(enable_profile=0):
                # 逐帧推理
                img=pl.get_frame()
                res=yolo.run(img)
                if res:
                    centers = []
                    for det in res:
                        x1, y1, x2, y2 = map(lambda x: int(round(x, 0)), det[:4])
                        raw_cx = (x1 + x2) // 2
                        raw_cy = (y1 + y2) // 2

                        disp_cx = raw_cx * yolo.display_size[0] // yolo.rgb888p_size[0]
                        disp_cy = raw_cy * yolo.display_size[1] // yolo.rgb888p_size[1]

                        label = yolo.labels[int(det[5])]

                        centers.append({
                                            "label": label,
                                            "raw": (raw_cx, raw_cy),
                                            "disp": (disp_cx, disp_cy)
                                        })
                    if centers:
                        for obj in centers:
                            print(f"{obj['label']}: 显示坐标({obj['disp'][0]},{obj['disp'][1]})")
                yolo.draw_result(res,pl.osd_img)
                pl.show_image()
                gc.collect()
    except Exception as e:
        sys.print_exception(e)
    finally:
        yolo.deinit()
        pl.destroy()

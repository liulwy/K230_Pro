import ujson
import nncase_runtime as nn
import ulab.numpy as np
import gc
import image
import aicube
from media.media import *
import os

class ObjectDetector:
    def __init__(self, config_path, root_path=""):
        # 获取配置文件的目录路径
        # 在MicroPython中直接使用字符串操作
        # 找到最后一个斜杠的位置来确定目录
        last_slash = config_path.rfind('/')
        config_dir = config_path[:last_slash + 1] if last_slash != -1 else ""
        
        # 读取配置文件
        with open(config_path, 'r') as json_file:
            deploy_conf = ujson.load(json_file)
            
        # 处理kmodel路径
        kmodel_name = deploy_conf["kmodel_path"]
        
        # 路径处理 - 使用字符串拼接
        if root_path:
            # 确保root_path以斜杠结尾
            self.kmodel_path = root_path + kmodel_name
        else:
            self.kmodel_path = config_dir + kmodel_name
        
        print(f"Loading kmodel from: {self.kmodel_path}")
        
        # 确保kmodel文件存在
        try:
            # 在MicroPython中检查文件是否存在的方式
            with open(self.kmodel_path, 'rb') as f:
                pass
        except OSError:
            raise OSError(f"KModel file not found: {self.kmodel_path}")
        
        # 其他配置参数
        self.labels = deploy_conf["categories"]
        self.confidence_threshold = deploy_conf["confidence_threshold"]
        self.nms_threshold = deploy_conf["nms_threshold"]
        self.img_size = deploy_conf["img_size"]
        self.num_classes = deploy_conf["num_classes"]
        self.nms_option = deploy_conf["nms_option"]
        self.model_type = deploy_conf["model_type"]
        
        if self.model_type == "AnchorBaseDet":
            self.anchors = (
                deploy_conf["anchors"][0] + 
                deploy_conf["anchors"][1] + 
                deploy_conf["anchors"][2]
            )
        
        self.strides = [8, 16, 32]  # 固定步长
        
        # 初始化模型
        self.kpu = nn.kpu()
        self.kpu.load_kmodel(self.kmodel_path)
        self.ai2d = nn.ai2d()
        self.ai2d.set_dtype(
            nn.ai2d_format.NCHW_FMT,
            nn.ai2d_format.NCHW_FMT,
            np.uint8, 
            np.uint8
        )
        
        # 初始化预处理参数
        self.preprocessing_set = False
        
        print("ObjectDetector initialized successfully")
    
    def preprocess(self, src_width, src_height):
        """计算预处理参数"""
        width, height = self.img_size
        ratiow = width / src_width
        ratioh = height / src_height
        ratio = min(ratiow, ratioh)
        
        new_w = int(ratio * src_width)
        new_h = int(ratio * src_height)
        
        dw = (width - new_w) / 2
        dh = (height - new_h) / 2
        
        top = int(round(dh - 0.1))
        bottom = int(round(dh + 0.1))
        left = int(round(dw - 0.1))
        right = int(round(dw + 0.1))
        
        # 设置预处理参数
        self.ai2d.set_pad_param(True, [0,0,0,0,top,bottom,left,right], 0, [114,114,114])
        self.ai2d.set_resize_param(True, nn.interp_method.tf_bilinear, nn.interp_mode.half_pixel)
        
        # 构建预处理器
        self.ai2d_builder = self.ai2d.build(
            [1, 3, src_height, src_width], 
            [1, 3, height, width]
        )
        
        self.preprocessing_set = True
    
    def process_frame(self, img):
        """处理单帧图像并返回检测结果"""
        if not self.preprocessing_set:
            self.preprocess(img.width(), img.height())
        
        # 准备输入输出张量
        ai2d_input = img.to_numpy_ref()
        ai2d_input_tensor = nn.from_numpy(ai2d_input)
        
        data = np.ones((1, 3, self.img_size[1], self.img_size[0]), dtype=np.uint8)
        ai2d_output_tensor = nn.from_numpy(data)
        
        # 预处理
        self.ai2d_builder.run(ai2d_input_tensor, ai2d_output_tensor)
        
        # 推理
        self.kpu.set_input_tensor(0, ai2d_output_tensor)
        self.kpu.run()
        
        # 获取输出
        results = []
        for i in range(self.kpu.outputs_size()):
            out_data = self.kpu.get_output_tensor(i)
            result = out_data.to_numpy()
            result = result.reshape(-1)  # 展平数组
            results.append(result)
            del out_data
        
        # 释放资源
        del ai2d_input_tensor
        del ai2d_output_tensor
        gc.collect()
        
        return results

    def postprocess(self, results, frame_width, frame_height):
        """后处理检测结果"""
        if self.model_type == "AnchorBaseDet":
            det_boxes = aicube.anchorbasedet_post_process(
                results[0], results[1], results[2], 
                self.img_size, 
                [frame_width, frame_height],
                self.strides, 
                self.num_classes, 
                self.confidence_threshold, 
                self.nms_threshold, 
                self.anchors, 
                self.nms_option
            )
        elif self.model_type == "GFLDet":
            det_boxes = aicube.gfldet_post_process(
                results[0], results[1], results[2], 
                self.img_size, 
                [frame_width, frame_height],
                self.strides, 
                self.num_classes, 
                self.confidence_threshold, 
                self.nms_threshold, 
                self.nms_option
            )
        else:  # AnchorFreeDet
            det_boxes = aicube.anchorfreedet_post_process(
                results[0], results[1], results[2], 
                self.img_size, 
                [frame_width, frame_height],
                self.strides, 
                self.num_classes, 
                self.confidence_threshold, 
                self.nms_threshold, 
                self.nms_option
            )
        
        return det_boxes
    
    def get_detection_results(self, img):
        """获取检测结果：返回(坐标, 标签, 置信度)"""
        # 获取图像尺寸
        frame_width = img.width()
        frame_height = img.height()
        
        # 处理帧
        results = self.process_frame(img)
        
        # 后处理
        det_boxes = self.postprocess(results, frame_width, frame_height)
        
        # 组织结果
        detections = []
        for box in det_boxes:
            # 解析检测结果元组
            class_id = int(box[0])
            confidence = float(box[1])
            x1 = float(box[2])
            y1 = float(box[3])
            x2 = float(box[4])
            y2 = float(box[5])
            
            # 转换为中心点坐标
            center_x = (x1 + x2) / 2
            center_y = (y1 + y2) / 2
            
            # 获取标签
            label = self.labels[class_id]
            
            detections.append({
                "coordinates": (x1, y1, x2, y2),  # 边界框坐标
                "center": (center_x, center_y),    # 中心点坐标
                "label": label,                    # 类别标签
                "class_id": class_id,              # 类别ID
                "confidence": confidence           # 置信度
            })
        
        # 清理内存
        gc.collect()
        
        return detections
    
    def __del__(self):
        """清理资源"""
        if hasattr(self, 'kpu'):
            print("Releasing KPU resources...")
            del self.kpu
        gc.collect()
        print("ObjectDetector resources released")
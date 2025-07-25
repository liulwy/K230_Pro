import os
import ujson
from time import *
import nncase_runtime as nn
import ulab.numpy as np
import time
import image
import gc
import utime

root_path="/sdcard/mp_deployment_source/"        # root_path要以/结尾
config_path=root_path+"deploy_config.json"
image_path=root_path+"test.jpg"
deploy_conf={}
debug_mode=1

class ScopedTiming:
    def __init__(self, info="", enable_profile=True):
        self.info = info
        self.enable_profile = enable_profile

    def __enter__(self):
        if self.enable_profile:
            self.start_time = time.time_ns()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self.enable_profile:
            elapsed_time = time.time_ns() - self.start_time
            print(f"{self.info} took {elapsed_time / 1000000:.2f} ms")

def read_img(img_path):
    img_data = image.Image(img_path)
    img_data_rgb888=img_data.to_rgb888()
    img_hwc=img_data_rgb888.to_numpy_ref()
    shape=img_hwc.shape
    img_tmp = img_hwc.reshape((shape[0] * shape[1], shape[2]))
    img_tmp_trans = img_tmp.transpose()
    img_res=img_tmp_trans.copy()
    img_return=img_res.reshape((shape[2],shape[0],shape[1]))
    return img_return

# 读取deploy_config.json文件
def read_deploy_config(config_path):
    # 打开JSON文件以进行读取deploy_config
    with open(config_path, 'r') as json_file:
        try:
            # 从文件中加载JSON数据
            config = ujson.load(json_file)

            # 打印数据（可根据需要执行其他操作）
            #print(config)
        except ValueError as e:
            print("JSON 解析错误:", e)
    return config

# 任务后处理
def softmax(x):
    exp_x = np.exp(x - np.max(x))
    return exp_x / np.sum(exp_x)

def sigmoid(x):
    return 1 / (1 + np.exp(-x))

def classification():
    print("--------------start-----------------")
    # 使用json读取内容初始化部署变量
    deploy_conf=read_deploy_config(config_path)
    kmodel_name=deploy_conf["kmodel_path"]
    labels=deploy_conf["categories"]
    confidence_threshold=deploy_conf["confidence_threshold"]
    img_size=deploy_conf["img_size"]
    num_classes=deploy_conf["num_classes"]
    cls_idx=-1

    # ai2d输入输出初始化
    ai2d_input = read_img(image_path)
    ai2d_input_tensor = nn.from_numpy(ai2d_input)
    ai2d_input_shape=ai2d_input.shape
    data = np.ones((1,3,img_size[0],img_size[1]),dtype=np.uint8)
    ai2d_out = nn.from_numpy(data)

    # init kpu and load kmodel
    kpu = nn.kpu()
    ai2d = nn.ai2d()
    kpu.load_kmodel(root_path+kmodel_name)
    ai2d.set_dtype(nn.ai2d_format.NCHW_FMT,
                                   nn.ai2d_format.NCHW_FMT,
                                   np.uint8, np.uint8)
    ai2d.set_resize_param(True, nn.interp_method.tf_bilinear, nn.interp_mode.half_pixel )
    ai2d_builder = ai2d.build([1,3,ai2d_input_shape[1],ai2d_input_shape[2]], [1,3,img_size[0],img_size[1]])
    with ScopedTiming("total",debug_mode > 0):
        ai2d_builder.run(ai2d_input_tensor, ai2d_out)
        kpu.set_input_tensor(0, ai2d_out)
        kpu.run()
        del ai2d_input_tensor
        del ai2d_out
        # 获取分类结果
        results = []
        for i in range(kpu.outputs_size()):
            data = kpu.get_output_tensor(i)
            result = data.to_numpy()
            results.append(result)
        # 后处理
        if num_classes>2:
            softmax_res=softmax(results[0][0])
            res_idx=np.argmax(softmax_res)
            if softmax_res[res_idx]>confidence_threshold:
                cls_idx=res_idx
                print("classification result:")
                print(labels[res_idx])
                print("score",softmax_res[cls_idx])
                image_draw=image.Image(image_path).to_rgb565()
                image_draw.draw_string(10, 10,labels[cls_idx] , scale=2,color=(255,0,255,0))
                image_draw.compress_for_ide()
                image_draw.save(root_path+"cls_result.jpg")
            else:
                cls_idx=-1
        else:
            sigmoid_res=sigmoid(results[0][0][0])
            if sigmoid_res>confidence_threshold:
                cls_idx=1
                print("classification result:")
                print(labels[cls_idx])
                print("score",sigmoid_res)
                image_draw=image.Image(image_path).to_rgb565()
                image_draw.draw_string(10, 10,labels[cls_idx] , scale=2,color=(255,0,255,0))
                image_draw.compress_for_ide()
                image_draw.save(root_path+"cls_result.jpg")
            else:
                cls_idx=0
                print("classification result:")
                print(labels[cls_idx])
                print("score",1-sigmoid_res)
                image_draw=image.Image(image_path).to_rgb565()
                image_draw.draw_string(10, 10,labels[cls_idx] , scale=2,color=(255,0,255,0))
                image_draw.compress_for_ide()
                image_draw.save(root_path+"cls_result.jpg")
        del data

    del ai2d
    del ai2d_builder
    del kpu
    print("---------------end------------------")
    gc.collect()
    nn.shrink_memory_pool()

if __name__=="__main__":
    nn.shrink_memory_pool()
    classification()

/* Copyright (c) 2023, Canaan Bright Sight Co., Ltd
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are met:
 * 1. Redistributions of source code must retain the above copyright
 * notice, this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright
 * notice, this list of conditions and the following disclaimer in the
 * documentation and/or other materials provided with the distribution.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND
 * CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES,
 * INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
 * DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
 * CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
 * SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
 * BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
 * SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
 * INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
 * WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
 * NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
 * OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */
// utils.h
#ifndef UTILS_H
#define UTILS_H

#include <algorithm>
#include <vector>
#include <iostream>
#include <fstream>
#include <opencv2/core.hpp>
#include <opencv2/highgui.hpp>
#include <opencv2/imgcodecs.hpp>
#include <opencv2/imgproc.hpp>
#include <nncase/functional/ai2d/ai2d_builder.h>

#include <string>
#include <string.h>
#include <cmath>
#include <stdio.h>
#include <stdlib.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <sys/ioctl.h>
#include <unistd.h>
#include <stdint.h>
#include <random>
#include "json.h"


using namespace nncase;
using namespace nncase::runtime;
using namespace nncase::runtime::k230;
using namespace nncase::F::k230;


using namespace std;
using namespace cv;
using cv::Mat;
using std::cout;
using std::endl;
using std::ifstream;
using std::vector;

#define STAGE_NUM 3
#define STRIDE_NUM 3
#define LABELS_NUM 1
#define ANCHORS_NUM 3

#define WORD_ENCODE "Asci0816.zf"
#define CHINESE_ENCODE "HZKf2424.hz"

// 颜色盘 三通道
const std::vector<cv::Scalar> color_three = {cv::Scalar(220, 20, 60), cv::Scalar(119, 11, 32), cv::Scalar(0, 0, 142), cv::Scalar(0, 0, 230),
        cv::Scalar(106, 0, 228), cv::Scalar(0, 60, 100), cv::Scalar(0, 80, 100), cv::Scalar(0, 0, 70),
        cv::Scalar(0, 0, 192), cv::Scalar(250, 170, 30), cv::Scalar(100, 170, 30), cv::Scalar(220, 220, 0),
        cv::Scalar(175, 116, 175), cv::Scalar(250, 0, 30), cv::Scalar(165, 42, 42), cv::Scalar(255, 77, 255),
        cv::Scalar(0, 226, 252), cv::Scalar(182, 182, 255), cv::Scalar(0, 82, 0), cv::Scalar(120, 166, 157),
        cv::Scalar(110, 76, 0), cv::Scalar(174, 57, 255), cv::Scalar(199, 100, 0), cv::Scalar(72, 0, 118),
        cv::Scalar(255, 179, 240), cv::Scalar(0, 125, 92), cv::Scalar(209, 0, 151), cv::Scalar(188, 208, 182),
        cv::Scalar(0, 220, 176), cv::Scalar(255, 99, 164), cv::Scalar(92, 0, 73), cv::Scalar(133, 129, 255),
        cv::Scalar(78, 180, 255), cv::Scalar(0, 228, 0), cv::Scalar(174, 255, 243), cv::Scalar(45, 89, 255),
        cv::Scalar(134, 134, 103), cv::Scalar(145, 148, 174), cv::Scalar(255, 208, 186),
        cv::Scalar(197, 226, 255), cv::Scalar(171, 134, 1), cv::Scalar(109, 63, 54), cv::Scalar(207, 138, 255),
        cv::Scalar(151, 0, 95), cv::Scalar(9, 80, 61), cv::Scalar(84, 105, 51), cv::Scalar(74, 65, 105),
        cv::Scalar(166, 196, 102), cv::Scalar(208, 195, 210), cv::Scalar(255, 109, 65), cv::Scalar(0, 143, 149),
        cv::Scalar(179, 0, 194), cv::Scalar(209, 99, 106), cv::Scalar(5, 121, 0), cv::Scalar(227, 255, 205),
        cv::Scalar(147, 186, 208), cv::Scalar(153, 69, 1), cv::Scalar(3, 95, 161), cv::Scalar(163, 255, 0),
        cv::Scalar(119, 0, 170), cv::Scalar(0, 182, 199), cv::Scalar(0, 165, 120), cv::Scalar(183, 130, 88),
        cv::Scalar(95, 32, 0), cv::Scalar(130, 114, 135), cv::Scalar(110, 129, 133), cv::Scalar(166, 74, 118),
        cv::Scalar(219, 142, 185), cv::Scalar(79, 210, 114), cv::Scalar(178, 90, 62), cv::Scalar(65, 70, 15),
        cv::Scalar(127, 167, 115), cv::Scalar(59, 105, 106), cv::Scalar(142, 108, 45), cv::Scalar(196, 172, 0),
        cv::Scalar(95, 54, 80), cv::Scalar(128, 76, 255), cv::Scalar(201, 57, 1), cv::Scalar(246, 0, 122),
        cv::Scalar(191, 162, 208)};

// 颜色盘 四通道
const std::vector<cv::Scalar> color_four = {cv::Scalar(255, 220, 20, 60), cv::Scalar(255, 119, 11, 32), cv::Scalar(255, 0, 0, 142), cv::Scalar(255, 0, 0, 230),
        cv::Scalar(255, 106, 0, 228), cv::Scalar(255, 0, 60, 100), cv::Scalar(255, 0, 80, 100), cv::Scalar(255, 0, 0, 70),
        cv::Scalar(255, 0, 0, 192), cv::Scalar(255, 250, 170, 30), cv::Scalar(255, 100, 170, 30), cv::Scalar(255, 220, 220, 0),
        cv::Scalar(255, 175, 116, 175), cv::Scalar(255, 250, 0, 30), cv::Scalar(255, 165, 42, 42), cv::Scalar(255, 255, 77, 255),
        cv::Scalar(255, 0, 226, 252), cv::Scalar(255, 182, 182, 255), cv::Scalar(255, 0, 82, 0), cv::Scalar(255, 120, 166, 157),
        cv::Scalar(255, 110, 76, 0), cv::Scalar(255, 174, 57, 255), cv::Scalar(255, 199, 100, 0), cv::Scalar(255, 72, 0, 118),
        cv::Scalar(255, 255, 179, 240), cv::Scalar(255, 0, 125, 92), cv::Scalar(255, 209, 0, 151), cv::Scalar(255, 188, 208, 182),
        cv::Scalar(255, 0, 220, 176), cv::Scalar(255, 255, 99, 164), cv::Scalar(255, 92, 0, 73), cv::Scalar(255, 133, 129, 255),
        cv::Scalar(255, 78, 180, 255), cv::Scalar(255, 0, 228, 0), cv::Scalar(255, 174, 255, 243), cv::Scalar(255, 45, 89, 255),
        cv::Scalar(255, 134, 134, 103), cv::Scalar(255, 145, 148, 174), cv::Scalar(255, 255, 208, 186),
        cv::Scalar(255, 197, 226, 255), cv::Scalar(255, 171, 134, 1), cv::Scalar(255, 109, 63, 54), cv::Scalar(255, 207, 138, 255),
        cv::Scalar(255, 151, 0, 95), cv::Scalar(255, 9, 80, 61), cv::Scalar(255, 84, 105, 51), cv::Scalar(255, 74, 65, 105),
        cv::Scalar(255, 166, 196, 102), cv::Scalar(255, 208, 195, 210), cv::Scalar(255, 255, 109, 65), cv::Scalar(255, 0, 143, 149),
        cv::Scalar(255, 179, 0, 194), cv::Scalar(255, 209, 99, 106), cv::Scalar(255, 5, 121, 0), cv::Scalar(255, 227, 255, 205),
        cv::Scalar(255, 147, 186, 208), cv::Scalar(255, 153, 69, 1), cv::Scalar(255, 3, 95, 161), cv::Scalar(255, 163, 255, 0),
        cv::Scalar(255, 119, 0, 170), cv::Scalar(255, 0, 182, 199), cv::Scalar(255, 0, 165, 120), cv::Scalar(255, 183, 130, 88),
        cv::Scalar(255, 95, 32, 0), cv::Scalar(255, 130, 114, 135), cv::Scalar(255, 110, 129, 133), cv::Scalar(255, 166, 74, 118),
        cv::Scalar(255, 219, 142, 185), cv::Scalar(255, 79, 210, 114), cv::Scalar(255, 178, 90, 62), cv::Scalar(255, 65, 70, 15),
        cv::Scalar(255, 127, 167, 115), cv::Scalar(255, 59, 105, 106), cv::Scalar(255, 142, 108, 45), cv::Scalar(255, 196, 172, 0),
        cv::Scalar(255, 95, 54, 80), cv::Scalar(255, 128, 76, 255), cv::Scalar(255, 201, 57, 1), cv::Scalar(255, 246, 0, 122),
        cv::Scalar(255, 191, 162, 208)};

/**
 * @brief config配置参数
 */
typedef struct config_args
{
    int input_height;//kmodel输入的高度 
    int input_width;//kmodel输入的宽度
    float obj_thresh;//目标分数阈值
    float nms_thresh;//非极大值抑制阈值
    float mask_thresh;//掩码阈值
    float box_thresh;//ocr检测框阈值
    int num_class;//标签类别数
    int reg_max;//gfldet的区域数
    int dict_num;//ocr识别的字典大小
    int strides[3];//每个输出分辨率的缩减倍数
    bool fixed_length;//ocr识别是否是直接resize或者padding resize
    bool nms_option;
    string model_type;//任务模型类别名称
    string kmodel_path;//kmodel的路径
    float anchors[3][3][2];//预设锚框
    vector<string> labels;//标签类别名称
    vector<int> memory_bank_shape;//异常检测memory_bank形状信息
    float image_threshold;//异常检测分数阈值

}config_args;

/**
 * @brief 分类结果结构
 */
typedef struct cls_res
{
    float score;//分类分数
    string label;//分类标签结果
}cls_res;

/**
 * @brief 异常检测结果结构
 */
typedef struct anomaly_res
{
    float score;//异常分数
    string label;//推理结果
}anomaly_res;

/**
 * @brief 多目标检测的结果结构
 */
typedef struct ob_det_res
{
    float x1;//检测框左上角点横坐标
    float y1;//检测框左上角点纵坐标
    float x2;//检测框右下角点横坐标
    float y2;//检测框右下角点纵坐标
    float score;//检测框的分数
    int label_index;//检测分类类别索引
    string label;//健侧类别名称
}ob_det_res;

/**
 * @brief 多标签分类结果结构
 */
typedef struct multi_lable_res
{
    vector<float> score_vec;//多标签分类的分数集合
    vector<int> id_vec;//多标签分类的判别结果结合
    vector<string> labels;//多标签分类的名称集合
}multi_lable_res;

/**
 * @brief ocr检测结果结构
 */
typedef struct ocr_det_res
{
    float meanx;
    float meany;
	Point2f vertices[4];
    Point2f ver_src[4];
    float score;
}ocr_det_res;

/**
 * @brief 中心点对
 */
typedef struct CenterPrior
{
    int x;
    int y;
    int stride;
}CenterPrior;


/**
 * @brief 车牌检测框
 */
typedef struct Bbox
{
    float x; // 车牌检测框的左顶点x坐标
    float y; // 车牌检测框的左顶点y坐标
    float w;
    float h;
} Bbox;

/**
 * @brief 车牌检测索引
 */
typedef struct sortable_obj_t
{
	int index;
	float* probs;
} sortable_obj_t;

/**
 * @brief 车牌检测四个点的 x y值
 */
typedef struct landmarks_t
{
	float points[8];
} landmarks_t;

/**
 * @brief 车牌检测框点集合
 */
typedef struct BoxPoint
{
    Point2f vertices[4];
} BoxPoint;


/**
 * @brief 人脸五官点
 */
typedef struct SparseLandmarks
{
    float points[10]; // 人脸五官点,依次是图片的左眼（x,y）、右眼（x,y）,鼻子（x,y）,左嘴角（x,y）,右嘴角
} SparseLandmarks;

/**
 * @brief 单张/帧图片大小
 */
typedef struct FrameSize
{
    size_t width;  // 宽
    size_t height; // 高
} FrameSize;

/**
 * @brief 单张/帧图片大小
 */
typedef struct FrameCHWSize
{
    size_t channel; // 通道
    size_t height;  // 高
    size_t width;   // 宽
} FrameCHWSize;

typedef struct BoxInfo
{
    float x1;
    float y1;
    float x2;
    float y2;
    float score;
    int label;
} BoxInfo;

/**
 * @brief AI Demo工具类
 * 封装了AI Demo常用的函数，包括二进制文件读取、文件保存、图片预处理等操作
 */
class Utils
{
public:
    /**
     * @brief 读取2进制文件
     * @param file_name 文件路径
     * @return 文件对应类型的数据
     */
    template <class T>
    static vector<T> read_binary_file(const char *file_name)
    {
        ifstream ifs(file_name, std::ios::binary);
        ifs.seekg(0, ifs.end);
        size_t len = ifs.tellg();
        vector<T> vec(len / sizeof(T), 0);
        ifs.seekg(0, ifs.beg);
        ifs.read(reinterpret_cast<char *>(vec.data()), len);
        ifs.close();
        return vec;
    }

    /**
     * @brief 打印数据
     * @param data 需打印数据对应指针
     * @param size 需打印数据大小
     * @return None
     */
    template <class T>
    static void dump(const T *data, size_t size)
    {
        for (size_t i = 0; i < size; i++)
        {
            cout << data[i] << " ";
        }
        cout << endl;
    }

    // 静态成员函数不依赖于类的实例，可以直接通过类名调用
    /**
     * @brief 将数据以2进制方式保存为文件
     * @param file_name 保存文件路径+文件名
     * @param data      需要保存的数据
     * @param size      需要保存的长度
     * @return None
     */
    static void dump_binary_file(const char *file_name, char *data, const size_t size);

    /**
     * @brief 将数据保存为灰度图片
     * @param file_name  保存图片路径+文件名
     * @param frame_size 保存图片的宽、高
     * @param data       需要保存的数据
     * @return None
     */
    static void dump_gray_image(const char *file_name, const FrameSize &frame_size, unsigned char *data);

    /**
     * @brief 将数据保存为彩色图片
     * @param file_name  保存图片路径+文件名
     * @param frame_size 保存图片的宽、高
     * @param data       需要保存的数据
     * @return None
     */
    static void dump_color_image(const char *file_name, const FrameSize &frame_size, unsigned char *data);


    /*************************for img process********************/
    /**
     * @brief 对图片进行先padding后resize的处理
     * @param ori_img             原始图片
     * @param frame_size      需要resize图像的宽高
     * @param padding         需要padding的像素，默认是cv::Scalar(104, 117, 123),BGR
     * @return 处理后图像
     */
    static cv::Mat padding_resize(const cv::Mat img, const FrameSize &frame_size, const cv::Scalar &padding = cv::Scalar(104, 117, 123));

    /**
     * @brief 对图片resize
     * @param ori_img             原始图片
     * @param frame_size      需要resize图像的宽高
     * @param padding         需要padding的像素，默认是cv::Scalar(104, 117, 123),BGR
     * @return                处理后图像
     */
    static cv::Mat resize(const cv::Mat ori_img, const FrameSize &frame_size);

    /**
     * @brief 将图片从bgr转为rgb
     * @param ori_img         原始图片
     * @return                处理后图像
     */
    static cv::Mat bgr_to_rgb(cv::Mat ori_img);

    /**
     * @brief 将RGB或RGB图片从hwc转为chw
     * @param ori_img          原始图片
     * @param chw_vec          转为chw后的数据
     * @return None
     */
    static void hwc_to_chw(cv::Mat &ori_img, std::vector<uint8_t> &chw_vec); // for rgb data

    /**
     * @brief 将BGR图片从hwc转为chw
     * @param ori_img          原始图片
     * @param chw_vec          转为chw后的数据
     * @return None
     */
    static void bgr2rgb_and_hwc2chw(cv::Mat &ori_img, std::vector<uint8_t> &chw_vec);

    /*************************for ai2d ori_img process********************/
    // resize
    /**
     * @brief resize函数，对chw数据进行resize
     * @param ori_shape        原始数据chw
     * @param chw_vec          原始数据
     * @param ai2d_out_tensor  ai2d输出
     * @return None
     */
    static void resize(FrameCHWSize ori_shape, std::vector<uint8_t> &chw_vec, runtime_tensor &ai2d_out_tensor);

    /**
     * @brief resize函数
     * @param builder          ai2d构建器，用于运行ai2d
     * @param ai2d_in_tensor   ai2d输入
     * @param ai2d_out_tensor  ai2d输出
     * @return None
     */
    static void resize(std::unique_ptr<ai2d_builder> &builder, runtime_tensor &ai2d_in_tensor, runtime_tensor &ai2d_out_tensor);

    // crop resize
    /**
     * @brief resize函数，对chw数据进行crop & resize
     * @param builder          ai2d构建器，用于运行ai2d
     * @param ai2d_in_tensor   ai2d输入
     * @param ai2d_out_tensor  ai2d输出
     * @return None
     */
    static void crop_resize(FrameCHWSize ori_shape, std::vector<uint8_t> &chw_vec, Bbox &crop_info, runtime_tensor &ai2d_out_tensor);
    
    /**
     * @brief crop_resize函数，对chw数据进行crop & resize
     * @param crop_info        需要crop的位置，x,y,w,h
     * @param builder          ai2d构建器，用于运行ai2d
     * @param ai2d_in_tensor   ai2d输入
     * @param ai2d_out_tensor  ai2d输出
     * @return None
     */
    static void crop_resize(Bbox &crop_info, std::unique_ptr<ai2d_builder> &builder, runtime_tensor &ai2d_in_tensor, runtime_tensor &ai2d_out_tensor);

    // padding resize
    /**
     * @brief padding_resize函数（上下左右padding），对chw数据进行padding & resize
     * @param ori_shape        原始数据chw
     * @param chw_vec          原始数据
     * @param builder          ai2d构建器，用于运行ai2d
     * @param ai2d_in_tensor   ai2d输入
     * @param ai2d_out_tensor  ai2d输出
     * @return None
     */
    static void padding_resize(FrameCHWSize ori_shape, std::vector<uint8_t> &chw_vec, FrameSize resize_shape, runtime_tensor &ai2d_out_tensor, cv::Scalar padding);
    
    /**
     * @brief padding_resize函数（右或下padding），对chw数据进行padding & resize
     * @param ori_shape        原始数据chw
     * @param chw_vec          原始数据
     * @param resize_shape     resize之后的大小
     * @param ai2d_out_tensor  ai2d输出
     * @param padding          填充值，用于resize时的等比例变换
     * @return None
     */
    static void padding_resize_one_side(FrameCHWSize ori_shape, std::vector<uint8_t> &chw_vec, FrameSize resize_shape, runtime_tensor &ai2d_out_tensor, cv::Scalar padding);

    /**
     * @brief padding_resize函数（上下左右padding），对chw数据进行padding & resize
     * @param ori_shape        原始数据chw
     * @param resize_shape     resize之后的大小
     * @param builder          ai2d构建器，用于运行ai2d
     * @param ai2d_in_tensor   ai2d输入
     * @param ai2d_out_tensor  ai2d输出
     * @param padding          填充值，用于resize时的等比例变换
     * @return None
     */
    static void padding_resize(FrameCHWSize ori_shape, FrameSize resize_shape, std::unique_ptr<ai2d_builder> &builder, runtime_tensor &ai2d_in_tensor, runtime_tensor &ai2d_out_tensor, cv::Scalar padding);
    
    /**
     * @brief padding_resize函数（右或下padding），对chw数据进行padding & resize
     * @param ori_shape        原始数据chw
     * @param resize_shape     resize之后的大小
     * @param builder          ai2d构建器，用于运行ai2d
     * @param ai2d_in_tensor   ai2d输入
     * @param ai2d_out_tensor  ai2d输出
     * @param padding          填充值，用于resize时的等比例变换
     * @return None
     */
    static void padding_resize_one_side(FrameCHWSize ori_shape, FrameSize resize_shape, std::unique_ptr<ai2d_builder> &builder, runtime_tensor &ai2d_in_tensor, runtime_tensor &ai2d_out_tensor, const cv::Scalar padding);

    // affine
    /**
     * @brief 仿射变换函数，对chw数据进行仿射变换(for imgae)
     * @param ori_shape        原始数据chw大小
     * @param ori_data         原始数据
     * @param affine_matrix    仿射变换矩阵
     * @param ai2d_out_tensor  仿射变换后的数据
     * @return None
     */
    static void affine(FrameCHWSize ori_shape, std::vector<uint8_t> &ori_data, float *affine_matrix, runtime_tensor &ai2d_out_tensor);

    /**
     * @brief 仿射变换函数，对chw数据进行仿射变换(for video)
     * @param affine_matrix    仿射变换矩阵
     * @param builder          ai2d构建器，用于运行ai2d
     * @param ai2d_in_tensor   ai2d输入
     * @param ai2d_out_tensor  ai2d输出
     * @return None
     */
    static void affine(float *affine_matrix, std::unique_ptr<ai2d_builder> &builder, runtime_tensor &ai2d_in_tensor, runtime_tensor &ai2d_out_tensor);

    /**
     * @brief 将视频流的图像从rgb转换为bgr格式
     * @param frame_size            原始图像宽高
     * @param data                  输入图像数据指针
     * @param chw_bgr_vec           bgr格式的图像数据
     * @return None
     */
    static void chw_rgb2bgr(const FrameSize &frame_size, unsigned char *data, std::vector<uint8_t> &chw_bgr_vec);


    /**
     * @brief 获取config里的任务构建参数
     * @param config        任务参数文件地址
     * @param args          得到的参数各属性值
     * @return None
     */
    static void parse_args(string config, config_args& args);

    /**
     * @brief 将分类任务的结果绘制到图像上
     * @param frame         原始图像
     * @param results       分类的结果
     * @return None
     */
    static void draw_cls_res(cv::Mat& frame, vector<cls_res>& results);

    /**
     * @brief 将分类任务的结果绘制到屏幕的osd中
     * @param frame                 原始图像
     * @param results               分类的结果
     * @param osd_frame_size        osd的宽高
     * @param sensor_frame_size     sensor的宽高
     * @return None
     */
    static void draw_cls_res(cv::Mat& frame, vector<cls_res>& results, FrameSize osd_frame_size, FrameSize sensor_frame_size);

    /**
     * @brief 将分多目标检测任务的结果绘制到图像上
     * @param frame         原始图像
     * @param results       分多目标检测的结果
     * @return None
     */
    static void draw_ob_det_res(cv::Mat& frame, vector<ob_det_res>& results);

    /**
     * @brief 将多目标检测任务的结果绘制到屏幕的osd中
     * @param frame                 原始图像
     * @param results               多目标检测的结果
     * @param osd_frame_size        osd的宽高
     * @param sensor_frame_size     sensor的宽高
     * @return None
     */
    static void draw_ob_det_res(cv::Mat& frame, vector<ob_det_res>& results, FrameSize osd_frame_size, FrameSize sensor_frame_size);

    /**
     * @brief 将多标签分类任务的结果绘制到图像上
     * @param frame         原始图像
     * @param results       多标签分类的结果
     * @return None
     */
    static void draw_mlcls_res(cv::Mat& frame, vector<multi_lable_res>& results);

    /**
     * @brief 将多标签分类任务的结果绘制到屏幕的osd中
     * @param frame                 原始图像
     * @param results               多标签分类的结果
     * @param osd_frame_size        osd的宽高
     * @param sensor_frame_size     sensor的宽高
     * @return None
     */
    static void draw_mlcls_res(cv::Mat& frame, vector<multi_lable_res>& results, FrameSize osd_frame_size, FrameSize sensor_frame_size);


    /**
     * @brief 将ocr检测任务的结果绘制到图像上
     * @param frame         原始图像
     * @param results       ocr检测的结果
     * @return None
     */
    static void draw_ocr_det_res(cv::Mat& frame, vector<ocr_det_res>& results);

    /**
     * @brief 将ocr检测任务的结果绘制到屏幕的osd中
     * @param frame                 原始图像
     * @param results               ocr检测的结果
     * @param osd_frame_size        osd的宽高
     * @param sensor_frame_size     sensor的宽高
     * @return None
     */
    static void draw_ocr_det_res(cv::Mat& frame, vector<ocr_det_res>& results, FrameSize osd_frame_size, FrameSize sensor_frame_size);


    /**
     * @brief 将异常检测任务的结果绘制到图像上
     * @param frame         原始图像
     * @param results       分类的结果
     * @return None
     */
    static void draw_anomaly_res(cv::Mat& frame, vector<anomaly_res>& results);


    /**
     * @brief 透射变换后crop
     * @param src         原始图像
     * @param dst         处理后的图像
     * @param b           车牌检测出的四边形角点对
     * @param vtd         排序后的四边形角点对
     * @return None
     */
    static void warppersp(cv::Mat src, cv::Mat& dst, ocr_det_res b, std::vector<Point2f>& vtd);


    /**
     * @brief 单图 画英文
     * @param image       作图的图像
     * @param x_offset    写字起始横坐标
     * @param y_offset    写字起始纵坐标
     * @param offset      英文字符的偏移量
     * @return None
     */
    static void paint_ascii(cv::Mat& image,int x_offset,int y_offset,unsigned long offset);

    /**
     * @brief video 画英文
     * @param image       作图的图像
     * @param x_offset    写字起始横坐标
     * @param y_offset    写字起始纵坐标
     * @param offset      英文字符的偏移量
     * @return None
     */
    static void paint_ascii_video(cv::Mat& image,int x_offset,int y_offset,unsigned long offset);


    /**
     * @brief 单图 画中文
     * @param image       作图的图像
     * @param x_offset    写字起始横坐标
     * @param y_offset    写字起始纵坐标
     * @param offset      中文字符的偏移量
     * @return None
     */
    static void paint_chinese(cv::Mat& image,int x_offset,int y_offset,unsigned long offset);

    /**
     * @brief video 画中文
     * @param image       作图的图像
     * @param x_offset    写字起始横坐标
     * @param y_offset    写字起始纵坐标
     * @param offset      中文字符的偏移量
     * @return None
     */
    static void paint_chinese_video(cv::Mat& image,int x_offset,int y_offset,unsigned long offset);


    /**
     * @brief 将ocr识别任务的结果绘制到图像上
     * @param frame         原始图像
     * @param results       ocr识别的结果
     * @return None
     */
    static void draw_ocr_rec_res(cv::Mat& image, vector<unsigned char>& vec16);

    /**
     * @brief 单图 写文本
     * @param x_offset    作图起始横坐标
     * @param y_offset    作图起始纵坐标
     * @param image       作图的图像
     * @param vec16       文字的16进制表示
     * @return None
     */
    static void draw_ocr_text(int x_offset,int y_offset,cv::Mat& image,vector<unsigned char> vec16);

    /**
     * @brief video 写文本
     * @param x_offset              作图起始横坐标
     * @param y_offset              作图起始纵坐标
     * @param image                 作图的图像
     * @param vec16                 文字的16进制表示
     * @param osd_frame_size        osd宽高
     * @param sensor_frame_size     sensor宽高
     * @return None
     */
    static void draw_ocr_text(float x_offset,float y_offset,cv::Mat& image,vector<unsigned char> vec16, FrameSize osd_frame_size, FrameSize sensor_frame_size);
};

#endif

import os
import logging
import ffmpeg
import numpy as np
from typing import BinaryIO
from funasr import AutoModel
from funasr.utils.postprocess_utils import rich_transcription_postprocess

SAMPLE_RATE = 16000

# 模型加载
model_path = os.getenv("MODEL_PATH", "/opt/ccs/models/SenseVoiceSmall")
vad_path = os.getenv("VAD_PATH", "/opt/ccs/models/speech_fsmn_vad_zh-cn-16k-common-pytorch")

# 支持任意时长音频输入
vad_enable = os.getenv("VAD_ENABLE", True)

# 推理方式
device_type = os.getenv("DEVICE_TYPE", "cuda")

# 设置用于 CPU 内部操作并行性的线程数（在使用GPU时此设置不影响主要计算）
cpu_num = os.getenv("ncpu", 4)

# 语言
language = os.getenv("language", "zh")

batch_size = os.getenv("batch_size", 64)

use_itn = os.getenv("use_itn", True)

def initialize_model():
    """初始化语音识别模型"""
    if vad_enable:
        # 准确预测
        model = AutoModel(
            model=model_path,
            vad_model=vad_path,
            vad_kwargs={"max_single_segment_time": 30000},
            trust_remote_code=False,
            device=device_type,
            ncpu=cpu_num,
            disable_update=True
        )
    else:
        # 快速预测
        model = AutoModel(
            model=model_path,
            trust_remote_code=False,
            device=device_type,
            ncpu=cpu_num,
            disable_update=True
        )
    
    print(f"音频模型成功加载到 {device_type}")
    return model

def transcribe_audio(file_path: str, model=None) -> dict:
    """
    将音频文件转换为文字
    
    Args:
        file_path: 音频文件路径
        model: 可选的模型实例，如果为None则创建新实例

    Returns:
        dict: 包含转换后文字的字典
    """
    if model is None:
        model = initialize_model()

    try:
        # 读取音频文件
        data = load_audio(file_path)
        
        if data is None or len(data) == 0:
            return {"text": "", "error": "音频文件解码错误"}

        # 进行语音识别
        res = model.generate(
            input=data,
            cache={},
            language=language,
            use_itn=use_itn,
            merge_vad=True,
            batch_size=batch_size,
        )

        # 后处理结果
        result = rich_transcription_postprocess(res[0]["text"])
        return {"text": result}

    except Exception as e:
        logging.error(f"语音转文字失败: {str(e)}")
        return {"text": "", "error": str(e)}

def load_audio(file_path: str, sr: int = SAMPLE_RATE) -> np.ndarray:
    """
    加载音频文件并转换为正确的格式
    
    Args:
        file_path: 音频文件路径
        sr: 采样率

    Returns:
        np.ndarray: 音频数据
    """
    try:
        # 使用ffmpeg读取音频
        out, _ = (
            ffmpeg.input(file_path)
            .output("-", format="f32le", acodec="pcm_f32le", ac=1, ar=sr)
            .run(capture_stdout=True, capture_stderr=True)
        )
    except ffmpeg.Error as e:
        logging.error(f"音频解码失败: {str(e)}")
        return None

    return np.frombuffer(out, np.float32)

from .models import UserDescription
from .services.stt import transcribe_audio

def process_audio_task(description_id: int):
    """
    处理音频文件，将语音转换为文字
    
    Args:
        description_id: UserDescription模型实例的ID
    """
    try:
        # 获取用户描述实例
        description = UserDescription.objects.get(id=description_id)
        
        # 进行语音转文字
        result = transcribe_audio(description.audio.path)
        
        if "error" in result:
            # 处理错误
            description.text_content = f"语音转换失败: {result['error']}"
            description.processed = False
        else:
            # 更新文字内容
            description.text_content = result["text"]
            description.processed = True
        
        description.save()
        
        return True
    except UserDescription.DoesNotExist:
        return False
    except Exception as e:
        return False

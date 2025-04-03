import logging
import requests

logger = logging.getLogger('diagnosis')

class AIService:
    def __init__(self):
        self.base_url = "http://localhost:11434/api/generate"
        self.model = "qwen2.5:7b"

    def generate_questions(self, user_description):
        """
        根据用户症状描述生成相关问题
        
        Args:
            user_description (str): 用户症状描述

        Returns:
            list: 包含三个问题的列表
        """
        try:
            # 构建提示词
            prompt = f"""基于以下患者症状描述，生成3个最相关的医疗问题，以帮助进一步了解病情：
            
            患者描述：{user_description}
            
            请生成3个问题，每个问题应该：
            1. 针对性强，直接关联症状
            2. 有助于进一步诊断
            3. 简洁明了，易于回答
            
            注意：请直接返回3个问题，每个问题占一行，不要有编号或其他额外内容。"""

            # 调用Ollama API
            response = requests.post(
                self.base_url,
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "top_p": 0.9,
                    }
                }
            )
            
            if response.status_code != 200:
                raise Exception(f"Ollama API调用失败: {response.text}")

            # 处理响应
            response_text = response.json()["response"].strip()
            questions = [q.strip() for q in response_text.split('\n') if q.strip()][:3]
            
            if len(questions) != 3:
                raise ValueError("未能生成足够的问题")

            return questions

        except Exception as e:
            logger.error(f'Failed to generate questions: {str(e)}')
            raise

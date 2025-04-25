import logging
import requests
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

logger = logging.getLogger('diagnosis')

class AIService:
    def __init__(self):
        # DashScope配置
        self.dashscope_url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
        self.dashscope_api_key = os.getenv('DASHSCOPE_API_KEY')
        # 火山引擎配置
        self.volcano_url = "https://open.volcengineapi.com/v1/text_generation"
        self.volcano_api_key = os.getenv('VOLCANO_API_KEY')
        
        if not self.dashscope_api_key:
            raise ValueError("DASHSCOPE_API_KEY environment variable is not set")
        if not self.volcano_api_key:
            raise ValueError("VOLCANO_API_KEY environment variable is not set")

    def _call_dashscope(self, prompt):
        """调用阿里百炼API"""
        headers = {
            "Authorization": f"Bearer {self.dashscope_api_key}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(
            self.dashscope_url,
            headers=headers,
            json={
                "model": "qwen-max",
                "input": {
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                },
                "parameters": {
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "result_format": "text"
                }
            }
        )
        
        if response.status_code != 200:
            raise Exception(f"百炼API调用失败: {response.text}")
            
        return response.json()["output"]["text"].strip()

    def _call_volcano(self, prompt):
        """调用火山引擎API"""
        headers = {
            "Authorization": f"Bearer {self.volcano_api_key}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(
            self.volcano_url,
            headers=headers,
            json={
                "model": "chatglm3-6b",  # 使用ChatGLM3作为备选模型
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "parameters": {
                    "temperature": 0.7,
                    "top_p": 0.9
                }
            }
        )
        
        if response.status_code != 200:
            raise Exception(f"火山引擎API调用失败: {response.text}")
            
        return response.json()["output"]["text"].strip()

    def generate_questions(self, user_description):
        """
        根据用户症状描述生成相关问题
        
        Args:
            user_description (str): 用户症状描述

        Returns:
            list: 包含三个问题的列表
        """
        # 构建提示词
        prompt = f"""基于以下患者症状描述，生成3个最相关的医疗问题，以帮助进一步了解病情：
        
        患者描述：{user_description}
        
        请生成3个问题，每个问题应该：
        1. 针对性强，直接关联症状
        2. 有助于进一步诊断
        3. 简洁明了，易于回答
        
        注意：请直接返回3个问题，每个问题占一行，不要有编号或其他额外内容。"""

        try:
            # 首先尝试调用百炼API
            try:
                response_text = self._call_dashscope(prompt)
            except Exception as e:
                logger.warning(f"百炼API调用失败，尝试使用火山引擎: {str(e)}")
                response_text = self._call_volcano(prompt)

            # 处理响应
            questions = [q.strip() for q in response_text.split('\n') if q.strip()][:3]
            
            if len(questions) != 3:
                raise ValueError("未能生成足够的问题")

            return questions

        except Exception as e:
            logger.error(f'Failed to generate questions: {str(e)}')
            raise

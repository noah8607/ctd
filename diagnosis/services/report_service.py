import json
import logging
import requests
import os
from typing import List, Dict
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

logger = logging.getLogger(__name__)

class ReportGenerationService:
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

    def _call_dashscope(self, prompt: str) -> str:
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
        response.raise_for_status()
        
        result = response.json()
        if "output" not in result:
            raise Exception(f"百炼API返回格式错误: {result}")
            
        return result["output"]["text"].strip()

    def _call_volcano(self, prompt: str) -> str:
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
        response.raise_for_status()
        
        result = response.json()
        if "output" not in result or "text" not in result["output"]:
            raise Exception(f"火山引擎API返回格式错误: {result}")
            
        return result["output"]["text"].strip()
        
    def generate_report(self, user_description: str, qa_pairs: List[Dict[str, str]], treatment: bool = False) -> str:
        """
        生成诊断报告
        
        Args:
            user_description: 用户自述内容
            qa_pairs: 问答对列表，每个问答对包含 question 和 answer
            treatment: 是否生成治疗方案
            
        Returns:
            str: 生成的诊断报告
        """
        # 构建提示词
        prompt = self._build_prompt(user_description, qa_pairs, treatment)

        try:
            # 首先尝试调用百炼API
            try:
                report = self._call_dashscope(prompt)
            except Exception as e:
                logger.warning(f"百炼API调用失败，尝试使用火山引擎: {str(e)}")
                report = self._call_volcano(prompt)
                
            return report
            
        except Exception as e:
            logger.error(f"Failed to generate report: {str(e)}")
            return None
            
    def _build_prompt(self, user_description: str, qa_pairs: List[Dict[str, str]], treatment: bool = False) -> str:
        """构建提示词"""
        qa_text = "\n".join([
            f"问题{i+1}: {qa['question']}\n回答{i+1}: {qa['answer']}"
            for i, qa in enumerate(qa_pairs)
        ])
        
        if not treatment:
            return f"""你是一位经验丰富的中医主治医师，你要基于患者自述和问诊记录进行初步诊断，并生成一份中医诊断报告。请仔细分析以下信息：

患者自述：
{user_description}

问诊记录：
{qa_text}

请按照中医诊断的传统方法进行分析和总结，应该至少包含以下内容并且不要给出治疗方案：

**辨证论治**
- 分析八纲（阴阳、表里、寒热、虚实）
- 辨别病因病机
- 确定证型（如气虚、阳虚、痰湿等）

请用专业但通俗易懂的语言撰写报告，适当解释中医术语，确保患者能够理解。如果发现任何需要紧急就医的危险信号，请在报告中特别标注。在辨证论治时，请注意结合现代医学知识，确保诊断的科学性和安全性。不要输出任何落款信息
"""
        else:
            return f"""你是一位经验丰富的中医主治医师，基于以下患者信息和初步诊断，制定一份中医治疗方案：

患者自述：
{user_description}

问诊记录：
{qa_text}

请提供以下内容：
1. 推荐的中药方剂（如有）
2. 针灸建议（如适用）
3. 生活调理建议
4. 饮食指导
5. 注意事项和禁忌

请用专业但通俗易懂的语言撰写建议，确保患者能够理解。对于需要在专业医生指导下进行的治疗，请特别说明。不要输出任何落款信息。
"""
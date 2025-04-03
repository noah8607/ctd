import json
import logging
import requests
from typing import List, Dict

logger = logging.getLogger(__name__)

class ReportGenerationService:
    def __init__(self):
        self.base_url = "http://localhost:11434/api/generate"
        self.model = "qwen2.5:7b"
        
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
            # 调用 Ollama API
            response = requests.post(
                self.base_url,
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False
                }
            )
            response.raise_for_status()
            
            # 解析响应
            result = response.json()
            if "error" in result:
                logger.error(f"Error generating report: {result['error']}")
                return None
                
            return result["response"]
            
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
            return f"""你是一位经验丰富的中医主治医师，你要基于患者自述和问诊记录进行初步诊断，并生成一份中医治疗方案。请仔细分析以下信息：

患者自述：
{user_description}

问诊记录：
{qa_text}

请按照中医诊断的传统方法进行分析和总结，给出治疗方案，不要给出除了治疗方案以外的任何内容：

**治疗方案**
- 推荐适合的中药方剂
- 说明各味药材的功效
- 建议配合的针灸、推拿等治疗方法
"""
            
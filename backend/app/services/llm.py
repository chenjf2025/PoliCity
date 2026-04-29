"""
LLM服务 - 集成DeepSeek云端大模型
"""
import httpx
from typing import Optional, Dict, Any
from app.core.config import settings


class LLMService:
    """DeepSeek LLM服务"""

    def __init__(self):
        self.api_url = settings.DEEPSEEK_API_URL
        self.api_key = settings.DEEPSEEK_API_KEY
        self.model = settings.DEEPSEEK_MODEL

    def chat(
        self,
        messages: list,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> str:
        """
        调用DeepSeek API进行对话

        Args:
            messages: 对话消息列表 [{"role": "user", "content": "..."}]
            system_prompt: 系统提示词
            temperature: 温度参数
            max_tokens: 最大token数

        Returns:
            LLM生成的回复内容 (Markdown格式)
        """
        # 构建完整的消息列表
        full_messages = []
        if system_prompt:
            full_messages.append({
                "role": "system",
                "content": system_prompt
            })
        full_messages.extend(messages)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": full_messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        try:
            client = httpx.Client(timeout=60.0)
            try:
                response = client.post(self.api_url, json=payload, headers=headers)
                response.raise_for_status()
                result = response.json()
                return result["choices"][0]["message"]["content"]
            finally:
                client.close()
        except httpx.HTTPStatusError as e:
            return f"**API调用错误**: {e.response.status_code}\n\n请检查API Key是否正确配置。"
        except Exception as e:
            return f"**服务错误**: {str(e)}\n\n请稍后重试。"


class AgentAnalysisPrompter:
    """Agent分析提示词生成器"""

    @staticmethod
    def generate_policy_analysis_prompt(
        region_name: str,
        report_year: int,
        original_score: float,
        simulated_score: float,
        score_delta: float,
        dimension_changes: list,
        policy_changes: list
    ) -> str:
        """生成政策分析的提示词"""
        dim_changes_md = "\n".join([
            f"- **{d['dimension']}**: {d['original']} → {d['simulated']} ({d['delta']:+.2f})"
            for d in dimension_changes
        ]) if dimension_changes else "暂无维度变化数据"

        policy_md = "\n".join([
            f"- {p.get('indicator_code', '未知')}: {p.get('change_percent', 0):+.1f}%"
            for p in policy_changes
        ]) if policy_changes else "暂无政策调整"

        change_pct = (score_delta / original_score * 100) if original_score > 0 else 0
        return f"""## 政策仿真分析报告

### 基本信息
- **城市**: {region_name}
- **报告年份**: {report_year}
- **原始总分**: {original_score:.2f}
- **仿真后总分**: {simulated_score:.2f}
- **总分变化**: {score_delta:+.2f} ({change_pct:+.1f}%)

### 政策调整方案
{policy_md}

### 各维度影响分析
{dim_changes_md}

请基于以上数据，生成一份详细的政策分析报告，要求：
1. 分析政策调整对各维度的具体影响
2. 指出最有效的政策杠杆
3. 预警可能的负面影响
4. 提出针对性的政策建议

请使用Markdown格式输出，包含结构化的分析和可操作的建议。"""

    @staticmethod
    def generate_overall_analysis_prompt(
        region_name: str,
        report_year: int,
        total_score: float,
        dimension_scores: Dict[str, float],
        shortboards: list
    ) -> str:
        """生成总体分析的提示词"""
        scores_md = "\n".join([
            f"- **{dim}**: {score:.1f}分"
            for dim, score in dimension_scores.items()
        ]) if dimension_scores else "暂无数据"

        shortboards_md = "\n".join([
            f"- {s.get('indicator_name', s.get('dimension', '未知'))}: {s.get('score', s.get('gap', 0)):.1f}分"
            for s in shortboards[:5]
        ]) if shortboards else "暂无明显短板"

        return f"""## 城市发展体检报告

### 基本信息
- **城市**: {region_name}
- **报告年份**: {report_year}
- **综合发展指数**: {total_score:.1f}分

### 五维评价得分
{scores_md}

### 短板预警指标
{shortboards_md}

请基于以上数据，生成一份全面的城市发展分析报告，要求：
1. 总体评价城市发展的优势和亮点
2. 深入分析制约发展的关键短板
3. 对标先进城市提出改进路径
4. 制定可落地的政策建议

请使用Markdown格式输出，包含结构化的分析和可操作的建议。"""


# 全局LLM服务实例
llm_service = LLMService()

"""
极差标准化处理器 (Min-Max Normalization)
正向指标: P = (x - min) / (max - min) * 100
负向指标: P = (max - x) / (max - min) * 100
"""
from typing import Dict, List, Tuple
import numpy as np


class Normalizer:
    """极差标准化处理器"""

    @staticmethod
    def normalize(raw_value: float, min_val: float, max_val: float, polarity: int) -> float:
        """
        对单个值进行极差标准化

        Args:
            raw_value: 原始数值
            min_val: 当前指标的最小值
            max_val: 当前指标的最大值
            polarity: 1=正向指标, -1=负向指标

        Returns:
            标准化得分 [0, 100]
        """
        if max_val == min_val:
            return 50.0  # 避免除零，返回中间值

        if polarity == 1:
            # 正向指标：值越大得分越高
            score = (raw_value - min_val) / (max_val - min_val) * 100
        else:
            # 负向指标：值越小得分越高
            score = (max_val - raw_value) / (max_val - min_val) * 100

        return round(max(0.0, min(100.0, score)), 2)

    @staticmethod
    def normalize_batch(
        raw_values: List[float],
        min_vals: List[float],
        max_vals: List[float],
        polarities: List[int]
    ) -> List[float]:
        """
        批量标准化处理

        Args:
            raw_values: 原始数值列表
            min_vals: 最小值列表
            max_vals: 最大值列表
            polarities: 极性列表

        Returns:
            标准化得分列表
        """
        scores = []
        for raw, min_v, max_v, pol in zip(raw_values, min_vals, max_vals, polarities):
            scores.append(Normalizer.normalize(raw, min_v, max_v, pol))
        return scores

    @staticmethod
    def calculate_bounds(values: List[float], method: str = "minmax") -> Tuple[float, float]:
        """
        计算标准化边界

        Args:
            values: 指标的所有历史值
            method: "minmax" 使用实际极值

        Returns:
            (min_val, max_val)
        """
        if not values:
            return 0.0, 100.0

        return float(min(values)), float(max(values))

    @staticmethod
    def calculate_percentile_bounds(values: List[float], low: float = 5, high: float = 95) -> Tuple[float, float]:
        """
        使用百分位数计算边界（用于异常值处理）

        Args:
            values: 指标的所有历史值
            low: 低百分位
            high: 高百分位

        Returns:
            (min_val, max_val)
        """
        if not values:
            return 0.0, 100.0

        arr = np.array(values)
        return float(np.percentile(arr, low)), float(np.percentile(arr, high))

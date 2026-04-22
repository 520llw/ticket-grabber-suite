"""Engines package - ticket grabbing engines registration.

免责声明：本工具仅供学习研究使用，禁止用于商业用途或黄牛行为。
"""
from .damai import DamaiEngine
from .maoyan import MaoyanEngine
from .train import Train12306Engine

ENGINE_MAP = {
    "damai": DamaiEngine,
    "maoyan": MaoyanEngine,
    "12306": Train12306Engine,
}

__all__ = ["DamaiEngine", "MaoyanEngine", "Train12306Engine", "ENGINE_MAP"]

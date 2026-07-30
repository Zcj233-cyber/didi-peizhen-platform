"""距离计算工具"""
import math


def haversine_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """
    计算两点间的直线距离（单位：公里）
    使用 Haversine 公式
    """
    R = 6371  # 地球半径（公里）

    d_lat = math.radians(lat2 - lat1)
    d_lng = math.radians(lng2 - lng1)
    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lng / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 1)

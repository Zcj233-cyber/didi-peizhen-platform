"""高德地图工具"""
from app.config import AMAP_KEY, AMAP_STATIC_MAP_URL


def get_static_map_url(latitude: str, longitude: str, hospital_name: str = "") -> str:
    """
    生成高德静态地图URL（显示地图图片）
    可直接用于 <img> 标签的 src
    """
    if not latitude or not longitude or AMAP_KEY == "你的高德地图Web服务Key":
        return ""

    lng, lat = longitude, latitude
    params = (
        f"?location={lng},{lat}"
        f"&zoom=15"
        f"&size=400*300"
        f"&key={AMAP_KEY}"
    )
    return f"{AMAP_STATIC_MAP_URL}{params}"

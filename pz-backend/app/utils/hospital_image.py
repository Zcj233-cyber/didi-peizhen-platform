"""从高德地图获取医院真实图片"""
import httpx
from typing import Optional
from app.config import AMAP_KEY

# 医院名称 → 搜索关键词映射（实测可用）
HOSPITAL_SEARCH_MAP = {
    "北京协和医院": ("北京协和医院", "北京"),
    "北京大学第三医院": ("北京大学第三医院", "北京"),
    "北京同仁医院": ("北京同仁医院", "北京"),
    "上海交通大学医学院附属瑞金医院": ("上海瑞金医院", "上海"),
    "复旦大学附属华山医院": ("复旦大学附属华山医院", "上海"),
    "上海长海医院": ("长海医院", "上海"),
    "中山大学附属第一医院": ("中山大学附属第一医院", "广州"),
    "南方医科大学南方医院": ("南方医院", "广州"),
    "华中科技大学同济医学院附属协和医院": ("武汉协和医院", "武汉"),
    "武汉大学人民医院": ("武汉大学人民医院", "武汉"),
    "四川大学华西医院": ("华西医院", "成都"),
    "四川省人民医院": ("四川省人民医院", "成都"),
    "北京大学深圳医院": ("北京大学深圳医院", "深圳"),
    "深圳市人民医院": ("深圳市人民医院", "深圳"),
    "浙江大学医学院附属第一医院": ("浙江大学医学院附属第一医院", "杭州"),
    "浙江省人民医院": ("浙江省人民医院", "杭州"),
}


async def fetch_hospital_image(hospital_name: str) -> Optional[str]:
    """从高德POI搜索获取医院真实图片"""
    if AMAP_KEY == "你的高德地图Web服务Key":
        return None

    search_info = HOSPITAL_SEARCH_MAP.get(hospital_name)
    if not search_info:
        return None

    keyword, city = search_info
    url = (
        f"https://restapi.amap.com/v3/place/text"
        f"?keywords={keyword}"
        f"&types=医院"
        f"&city={city}"
        f"&offset=1"
        f"&key={AMAP_KEY}"
    )

    try:
        async with httpx.AsyncClient(timeout=8) as client:
            resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
            data = resp.json()
            if data.get("status") == "1":
                pois = data.get("pois", [])
                if pois:
                    photos = pois[0].get("photos", [])
                    if photos:
                        for ph in photos:
                            img_url = ph.get("url", "")
                            if "store.is.autonavi.com" in img_url:
                                return img_url
                        return photos[0].get("url", "")
    except Exception:
        pass

    return None


async def batch_fetch_hospital_images() -> dict:
    """批量获取所有医院的真实图片"""
    result = {}
    for hospital_name in HOSPITAL_SEARCH_MAP:
        img = await fetch_hospital_image(hospital_name)
        if img:
            result[hospital_name] = img
            print(f"  [OK] {hospital_name}")
        else:
            print(f"  [--] {hospital_name}")
    return result

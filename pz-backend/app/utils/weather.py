"""天气查询工具"""
import httpx
import random
from datetime import datetime
from typing import Optional

# 模拟的中国城市天气数据（备用）
SIMULATED_WEATHER = {
    "北京": {"condition": "晴", "temp": 28, "wind": "3级", "humidity": 30, "pm25": 55},
    "上海": {"condition": "多云", "temp": 30, "wind": "3级", "humidity": 65, "pm25": 48},
    "广州": {"condition": "雷阵雨", "temp": 33, "wind": "2级", "humidity": 78, "pm25": 42},
    "武汉": {"condition": "晴", "temp": 35, "wind": "2级", "humidity": 55, "pm25": 72},
    "成都": {"condition": "阴", "temp": 27, "wind": "1级", "humidity": 70, "pm25": 68},
}

CONDITION_MAP = {
    "sunny": "晴", "clear": "晴", "cloudy": "多云", "partly cloudy": "多云",
    "overcast": "阴", "rain": "雨", "light rain": "小雨", "heavy rain": "大雨",
    "drizzle": "毛毛雨", "thunderstorm": "雷阵雨", "snow": "雪", "fog": "雾",
    "mist": "薄雾", "haze": "霾",
}


async def fetch_weather(city: str = "北京") -> dict:
    """获取天气数据（优先真实API，失败用模拟）"""
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            resp = await client.get(
                f"https://wttr.in/{city}?format=%C|%t|%w|%h|%p",
                headers={"Accept": "text/plain"},
            )
            if resp.status_code == 200:
                parts = resp.text.strip().split("|")
                condition_raw = parts[0].strip() if len(parts) > 0 else ""
                temp_raw = parts[1].strip() if len(parts) > 1 else ""
                wind_raw = parts[2].strip() if len(parts) > 2 else ""
                humidity_raw = parts[3].strip() if len(parts) > 3 else ""

                # 解析温度数字
                temp_str = "".join(c for c in temp_raw if c.isdigit() or c == "-")
                temp = int(temp_str) if temp_str else 25

                # 映射中文天气
                condition = condition_raw.lower()
                for eng, chn in CONDITION_MAP.items():
                    if eng in condition:
                        condition = chn
                        break
                else:
                    condition = condition_raw

                return {
                    "city": city,
                    "condition": condition,
                    "temperature": temp,
                    "wind": wind_raw or "未知",
                    "humidity": humidity_raw or "未知",
                    "source": "realtime",
                }
    except Exception:
        pass

    # 模拟降级
    sim = SIMULATED_WEATHER.get(city, SIMULATED_WEATHER["北京"])
    hour = datetime.now().hour
    if 6 <= hour < 9:
        sim["condition"] = "晴" if random.random() > 0.3 else "多云"
    elif 18 <= hour < 22:
        sim["condition"] = "多云" if random.random() > 0.3 else "阴"
    sim["temperature"] = sim["temp"] + random.randint(-3, 3)
    return {
        "city": city,
        "condition": sim["condition"],
        "temperature": sim["temperature"],
        "wind": sim["wind"],
        "humidity": f"{sim['humidity']}%",
        "source": "simulated",
    }


def get_travel_advice(weather: dict, dest_name: str = "医院") -> str:
    """根据天气生成出行建议"""
    temp = weather["temperature"]
    condition = weather["condition"]
    wind = weather["wind"]
    advice = []

    # 温度建议
    if temp >= 35:
        advice.append("高温天气，注意防暑降温，建议携带遮阳伞、饮用水")
    elif temp <= 5:
        advice.append("低温天气，注意保暖防寒，建议穿着厚外套")
    elif temp <= 15:
        advice.append("温度偏低，建议穿着长袖外套")
    elif 20 <= temp <= 30:
        advice.append("天气宜人，适合出行")
    elif temp > 30:
        advice.append("天气较热，注意补充水分")

    # 天气状况建议
    rain_keywords = ["雨", "雷阵雨", "暴雨", "毛毛雨"]
    if any(k in condition for k in rain_keywords):
        advice.append("有降水，请携带雨具，路面湿滑注意安全")
    if "雪" in condition:
        advice.append("有降雪，注意防滑，建议穿防滑鞋")
    if "雾" in condition or "霾" in condition:
        advice.append("能见度较低，出行请注意交通安全")
    if "大风" in wind or any(w in wind for w in ["m/s" for _ in range(1)]) and any(
        w in wind for w in ["5", "6", "7", "8", "9"]
    ):
        advice.append("风力较大，注意防风")

    # 针对就医的特别建议
    if any(k in condition for k in ["雨", "雪", "雾", "霾"]):
        advice.append(f"建议提前出发前往{dest_name}，预留充足时间")
    else:
        advice.append(f"天气良好，适合前往{dest_name}就诊")

    return "；".join(advice)

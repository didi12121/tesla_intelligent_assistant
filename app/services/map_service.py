from __future__ import annotations

import requests

from config import AMAP_KEY


class MapService:

    BASE_URL = "https://restapi.amap.com/v5/place"

    def search_nearby(
        self,
        longitude: float,
        latitude: float,
        keyword: str,
        radius: int = 3000,
        page_size: int = 10,
    ) -> list[dict]:
        """高德周边搜索，返回附近的 POI 列表。"""
        url = f"{self.BASE_URL}/around"
        params = {
            "key": AMAP_KEY,
            "keywords": keyword,
            "location": f"{longitude},{latitude}",
            "radius": radius,
            "show_fields": "business",
            "page_size": page_size,
            "page_num": 1,
        }
        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()

        if data.get("status") != "1":
            raise Exception(f"高德搜索失败: {data.get('info', '未知错误')}")

        pois = data.get("pois", [])
        results = []
        for poi in pois:
            results.append({
                "name": poi.get("name", ""),
                "address": poi.get("address", ""),
                "distance": poi.get("distance", ""),
                "type": poi.get("type", ""),
                "tel": poi.get("tel", ""),
                "location": poi.get("location", ""),
            })
        return results

    def regeocode(self, longitude: float, latitude: float) -> dict:
        """逆地理编码：经纬度 → 地址。"""
        url = "https://restapi.amap.com/v3/geocode/regeo"
        params = {
            "key": AMAP_KEY,
            "location": f"{longitude},{latitude}",
        }
        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()

        if data.get("status") != "1":
            raise Exception(f"逆地理编码失败: {data.get('info', '未知错误')}")

        regeocode = data.get("regeocode", {})
        return {
            "address": regeocode.get("formatted_address", ""),
            "province": regeocode.get("addressComponent", {}).get("province", ""),
            "city": regeocode.get("addressComponent", {}).get("city", ""),
            "district": regeocode.get("addressComponent", {}).get("district", ""),
        }

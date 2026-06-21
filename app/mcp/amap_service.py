"""
高德地图 MCP 服务集成
"""
import httpx
from app.core.config import settings
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class AMapService:
    """高德地图服务"""
    
    def __init__(self):
        self.api_key = settings.AMAP_API_KEY
        self.base_url = "https://restapi.amap.com/v3"
    
    async def search_poi(self, keywords: str, city: str = "全国", 
                        types: str = "旅游景点") -> List[Dict]:
        """搜索 POI（兴趣点）"""
        url = f"{self.base_url}/place/text"
        params = {
            'key': self.api_key,
            'keywords': keywords,
            'city': city,
            'types': types,
            'offset': 20,
            'page': 1,
            'extensions': 'all'
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params, timeout=10.0)
                data = response.json()
                
                if data['status'] == '1' and 'pois' in data:
                    return self._format_poi_results(data['pois'])
                else:
                    logger.warning(f"AMap API error: {data.get('info', 'Unknown')}")
                    return []
        except Exception as e:
            logger.error(f"POI search error: {e}")
            return []
    
    def _format_poi_results(self, pois: List[Dict]) -> List[Dict]:
        """格式化 POI 结果"""
        formatted = []
        for poi in pois:
            formatted.append({
                'name': poi.get('name', ''),
                'location': poi.get('location', '').split(','),
                'address': poi.get('address', ''),
                'type': poi.get('type', ''),
                'rating': poi.get('biz_ext', {}).get('rating', 0),
                'price': poi.get('biz_ext', {}).get('cost', 0),
            })
        return formatted
    
    async def get_weather(self, city: str = "北京") -> Dict:
        """获取天气信息"""
        url = f"{self.base_url}/weather/weatherInfo"
        params = {
            'key': self.api_key,
            'city': city,
            'extensions': 'all'
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params, timeout=10.0)
                data = response.json()
                
                if data['status'] == '1' and 'forecasts' in data:
                    return data['forecasts'][0]
                else:
                    return {}
        except Exception as e:
            logger.error(f"Weather query error: {e}")
            return {}
    
    async def calculate_route(self, origin: str, destination: str, 
                             mode: str = "driving") -> Dict:
        """计算路线"""
        url = f"{self.base_url}/direction/{mode}"
        params = {
            'key': self.api_key,
            'origin': origin,
            'destination': destination,
            'extensions': 'all'
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params, timeout=10.0)
                data = response.json()
                
                if data['status'] == '1' and 'route' in data:
                    return data['route']
                else:
                    return {}
        except Exception as e:
            logger.error(f"Route calculation error: {e}")
            return {}
    
    async def get_place_details(self, place_id: str) -> Dict:
        """获取地点详情"""
        url = f"{self.base_url}/place/detail"
        params = {
            'key': self.api_key,
            'id': place_id,
            'extensions': 'all'
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params, timeout=10.0)
                data = response.json()
                
                if data['status'] == '1' and 'pois' in data:
                    return data['pois'][0] if data['pois'] else {}
                else:
                    return {}
        except Exception as e:
            logger.error(f"Place details error: {e}")
            return {}


# 全局高德服务实例
amap_service = AMapService()

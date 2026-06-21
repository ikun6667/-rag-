"""
MCP 工具定义 - 将高德地图服务封装为 LangChain Tools
支持 LLM 动态调用工具
"""
from langchain.tools import tool
from app.mcp.amap_service import amap_service
from typing import List, Dict
import json
import logging

logger = logging.getLogger(__name__)


@tool
async def search_poi(keywords: str, city: str = "全国", types: str = "旅游景点") -> str:
    """
    搜索兴趣点（POI），如景点、酒店、餐厅等。
    
    Args:
        keywords: 搜索关键词，如"故宫"、"酒店"等
        city: 城市名称，默认"全国"
        types: POI类型，可选值：
               - "旅游景点": 搜索景点
               - "住宿服务": 搜索酒店
               - "餐饮服务": 搜索餐厅
               - "购物服务": 搜索商场
    
    Returns:
        JSON格式的搜索结果列表，包含名称、地址、评分等信息
    """
    try:
        logger.info(f"Calling search_poi tool: keywords={keywords}, city={city}, types={types}")
        results = await amap_service.search_poi(
            keywords=keywords,
            city=city,
            types=types
        )
        return json.dumps(results, ensure_ascii=False)
    except Exception as e:
        logger.error(f"search_poi tool error: {e}")
        return json.dumps({"error": str(e)}, ensure_ascii=False)


@tool
async def get_weather(city: str = "北京") -> str:
    """
    获取指定城市的天气信息。
    
    Args:
        city: 城市名称，如"北京"、"上海"等
    
    Returns:
        JSON格式的天气信息，包括温度、湿度、风力、天气预报等
    """
    try:
        logger.info(f"Calling get_weather tool: city={city}")
        weather_data = await amap_service.get_weather(city=city)
        return json.dumps(weather_data, ensure_ascii=False)
    except Exception as e:
        logger.error(f"get_weather tool error: {e}")
        return json.dumps({"error": str(e)}, ensure_ascii=False)


@tool
async def calculate_route(origin: str, destination: str, mode: str = "driving") -> str:
    """
    计算两个地点之间的路线规划。
    
    Args:
        origin: 起点坐标或地址，格式："经度,纬度" 或 "地址文本"
        destination: 终点坐标或地址，格式："经度,纬度" 或 "地址文本"
        mode: 出行方式，可选值：
              - "driving": 驾车（默认）
              - "walking": 步行
              - "transit": 公共交通
              - "bicycling": 骑行
    
    Returns:
        JSON格式的路线信息，包括距离、时间、路径详情等
    """
    try:
        logger.info(f"Calling calculate_route tool: origin={origin}, destination={destination}, mode={mode}")
        route_data = await amap_service.calculate_route(
            origin=origin,
            destination=destination,
            mode=mode
        )
        return json.dumps(route_data, ensure_ascii=False)
    except Exception as e:
        logger.error(f"calculate_route tool error: {e}")
        return json.dumps({"error": str(e)}, ensure_ascii=False)


@tool
async def get_place_details(place_id: str) -> str:
    """
    获取指定地点的详细信息。
    
    Args:
        place_id: 地点ID（从search_poi结果中获取）
    
    Returns:
        JSON格式的地点详细信息，包括电话、营业时间、详细介绍等
    """
    try:
        logger.info(f"Calling get_place_details tool: place_id={place_id}")
        details = await amap_service.get_place_details(place_id=place_id)
        return json.dumps(details, ensure_ascii=False)
    except Exception as e:
        logger.error(f"get_place_details tool error: {e}")
        return json.dumps({"error": str(e)}, ensure_ascii=False)


# 导出所有工具列表
amap_tools = [
    search_poi,
    get_weather,
    calculate_route,
    get_place_details
]

# 工具描述（用于LLM理解）
TOOLS_DESCRIPTION = """
可用工具：
1. search_poi: 搜索景点、酒店、餐厅等兴趣点
2. get_weather: 查询城市天气信息
3. calculate_route: 计算两地之间的路线规划
4. get_place_details: 获取地点的详细信息

使用建议：
- 当用户询问景点时，使用 search_poi(types="旅游景点")
- 当用户询问酒店时，使用 search_poi(types="住宿服务")
- 当需要了解天气时，使用 get_weather
- 当需要规划路线时，使用 calculate_route
- 当需要某个地点的详细信息时，先使用 search_poi 获取 place_id，再使用 get_place_details
"""

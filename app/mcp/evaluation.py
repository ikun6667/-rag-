"""
MCP 工具调用成功率评估工具
用于测试工具调用的成功率和性能
"""
import json
import time
import asyncio
from typing import List, Dict, Any
from app.mcp.tools import search_poi, get_weather, calculate_route, get_place_details
from app.mcp.amap_service import amap_service
import logging

logger = logging.getLogger(__name__)


class ToolCallEvaluator:
    """工具调用评估器"""
    
    def __init__(self):
        self.test_cases = []
    
    def load_test_cases(self, test_cases_path: str = None):
        """
        加载测试用例
        
        Args:
            test_cases_path: 测试用例JSON文件路径，如果为None则使用默认测试集
        """
        if test_cases_path:
            with open(test_cases_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.test_cases = data.get('test_cases', [])
        else:
            # 使用默认测试用例（12个测试用例，覆盖所有工具和多种场景）
            self.test_cases = [
                {
                    "tool": "search_poi",
                    "params": {"keywords": "故宫", "city": "北京", "types": "旅游景点"},
                    "description": "搜索北京故宫景点"
                },
                {
                    "tool": "search_poi",
                    "params": {"keywords": "酒店", "city": "上海", "types": "住宿服务"},
                    "description": "搜索上海酒店"
                },
                {
                    "tool": "search_poi",
                    "params": {"keywords": "餐厅", "city": "成都", "types": "餐饮服务"},
                    "description": "搜索成都餐厅"
                },
                {
                    "tool": "search_poi",
                    "params": {"keywords": "西湖", "city": "杭州", "types": "旅游景点"},
                    "description": "搜索杭州西湖景点"
                },
                {
                    "tool": "get_weather",
                    "params": {"city": "北京"},
                    "description": "查询北京天气"
                },
                {
                    "tool": "get_weather",
                    "params": {"city": "杭州"},
                    "description": "查询杭州天气"
                },
                {
                    "tool": "get_weather",
                    "params": {"city": "西安"},
                    "description": "查询西安天气"
                },
                {
                    "tool": "calculate_route",
                    "params": {"origin": "北京站", "destination": "故宫", "mode": "driving"},
                    "description": "计算北京站到故宫的驾车路线"
                },
                {
                    "tool": "calculate_route",
                    "params": {"origin": "上海虹桥机场", "destination": "外滩", "mode": "transit"},
                    "description": "计算上海虹桥机场到外滩的公共交通路线"
                },
                {
                    "tool": "calculate_route",
                    "params": {"origin": "成都双流机场", "destination": "宽窄巷子", "mode": "driving"},
                    "description": "计算成都双流机场到宽窄巷子的驾车路线"
                },
                {
                    "tool": "calculate_route",
                    "params": {"origin": "西安北站", "destination": "兵马俑", "mode": "transit"},
                    "description": "计算西安北站到兵马俑的公共交通路线"
                },
                {
                    "tool": "calculate_route",
                    "params": {"origin": "杭州东站", "destination": "西湖", "mode": "walking"},
                    "description": "计算杭州东站到西湖的步行路线"
                }
            ]
        
        logger.info(f"Loaded {len(self.test_cases)} test cases")
    
    async def test_single_tool_call(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """
        测试单个工具调用
        
        Args:
            test_case: 测试用例字典
            
        Returns:
            测试结果字典
        """
        tool_name = test_case['tool']
        params = test_case['params']
        description = test_case.get('description', '')
        
        result = {
            'tool': tool_name,
            'params': params,
            'description': description,
            'success': False,
            'response_time': 0,
            'error': None,
            'result_preview': None
        }
        
        start_time = time.time()
        
        try:
            # 根据工具名称调用对应的函数
            # 注意：async @tool 装饰器创建的工具使用 .coroutine 属性而非 .func
            if tool_name == "search_poi":
                if hasattr(search_poi, 'coroutine') and search_poi.coroutine:
                    response = await search_poi.coroutine(**params)
                else:
                    response = await search_poi.func(**params)
            elif tool_name == "get_weather":
                if hasattr(get_weather, 'coroutine') and get_weather.coroutine:
                    response = await get_weather.coroutine(**params)
                else:
                    response = await get_weather.func(**params)
            elif tool_name == "calculate_route":
                if hasattr(calculate_route, 'coroutine') and calculate_route.coroutine:
                    response = await calculate_route.coroutine(**params)
                else:
                    response = await calculate_route.func(**params)
            elif tool_name == "get_place_details":
                if hasattr(get_place_details, 'coroutine') and get_place_details.coroutine:
                    response = await get_place_details.coroutine(**params)
                else:
                    response = await get_place_details.func(**params)
            else:
                raise ValueError(f"Unknown tool: {tool_name}")
            
            end_time = time.time()
            result['success'] = True
            result['response_time'] = end_time - start_time
            
            # 保存结果预览（前200字符）
            if isinstance(response, str):
                result['result_preview'] = response[:200]
            else:
                result['result_preview'] = str(response)[:200]
            
            logger.info(f"✓ {tool_name} call succeeded in {result['response_time']:.2f}s")
            
        except Exception as e:
            end_time = time.time()
            result['success'] = False
            result['response_time'] = end_time - start_time
            result['error'] = str(e)
            
            logger.error(f"✗ {tool_name} call failed: {e}")
        
        return result
    
    async def evaluate_all(self) -> Dict[str, Any]:
        """
        执行所有工具调用测试
        
        Returns:
            评估结果字典
        """
        if not self.test_cases:
            raise ValueError("No test cases loaded. Call load_test_cases first.")
        
        results = []
        success_count = 0
        total_time = 0
        
        print(f"\n{'='*60}")
        print(f"开始 MCP 工具调用成功率评估")
        print(f"{'='*60}\n")
        
        for i, test_case in enumerate(self.test_cases, 1):
            print(f"[{i}/{len(self.test_cases)}] 测试: {test_case.get('description', test_case['tool'])}")
            print(f"  工具: {test_case['tool']}")
            print(f"  参数: {json.dumps(test_case['params'], ensure_ascii=False)}")
            
            result = await self.test_single_tool_call(test_case)
            results.append(result)
            
            if result['success']:
                success_count += 1
                print(f"  ✓ 成功 (耗时: {result['response_time']:.2f}s)")
                if result['result_preview']:
                    preview = result['result_preview'].replace('\n', ' ')
                    print(f"  结果预览: {preview[:100]}...")
            else:
                print(f"  ✗ 失败: {result['error']}")
            
            total_time += result['response_time']
            print()
        
        # 计算统计指标
        success_rate = success_count / len(self.test_cases) * 100 if self.test_cases else 0
        avg_response_time = total_time / len(self.test_cases) if self.test_cases else 0
        
        # 按工具分组统计
        tool_stats = {}
        for result in results:
            tool_name = result['tool']
            if tool_name not in tool_stats:
                tool_stats[tool_name] = {
                    'total': 0,
                    'success': 0,
                    'failed': 0,
                    'total_time': 0
                }
            
            tool_stats[tool_name]['total'] += 1
            if result['success']:
                tool_stats[tool_name]['success'] += 1
            else:
                tool_stats[tool_name]['failed'] += 1
            tool_stats[tool_name]['total_time'] += result['response_time']
        
        # 计算每个工具的成功率和平均响应时间
        for tool_name, stats in tool_stats.items():
            stats['success_rate'] = stats['success'] / stats['total'] * 100 if stats['total'] > 0 else 0
            stats['avg_response_time'] = stats['total_time'] / stats['total'] if stats['total'] > 0 else 0
        
        # 输出总结
        print(f"\n{'='*60}")
        print(f"评估结果总结")
        print(f"{'='*60}")
        print(f"总测试用例数:        {len(self.test_cases)}")
        print(f"成功调用数:          {success_count}")
        print(f"失败调用数:          {len(self.test_cases) - success_count}")
        print(f"总体成功率:          {success_rate:.2f}%")
        print(f"平均响应时间:        {avg_response_time:.2f}s")
        print(f"总耗时:              {total_time:.2f}s")
        print(f"\n各工具详细统计:")
        print(f"{'-'*60}")
        
        for tool_name, stats in tool_stats.items():
            print(f"\n{tool_name}:")
            print(f"  调用次数:      {stats['total']}")
            print(f"  成功次数:      {stats['success']}")
            print(f"  失败次数:      {stats['failed']}")
            print(f"  成功率:        {stats['success_rate']:.2f}%")
            print(f"  平均响应时间:  {stats['avg_response_time']:.2f}s")
        
        print(f"\n{'='*60}\n")
        
        return {
            'total_tests': len(self.test_cases),
            'success_count': success_count,
            'failed_count': len(self.test_cases) - success_count,
            'success_rate': success_rate,
            'avg_response_time': avg_response_time,
            'total_time': total_time,
            'tool_statistics': tool_stats,
            'detailed_results': results
        }
    
    def save_results(self, results: Dict[str, Any], output_path: str = "tool_evaluation_results.json"):
        """
        保存评估结果到文件
        
        Args:
            results: 评估结果字典
            output_path: 输出文件路径
        """
        # 序列化结果
        serializable_results = {
            'total_tests': results['total_tests'],
            'success_count': results['success_count'],
            'failed_count': results['failed_count'],
            'success_rate': results['success_rate'],
            'avg_response_time': results['avg_response_time'],
            'total_time': results['total_time'],
            'tool_statistics': results['tool_statistics'],
            'detailed_results': [
                {
                    'tool': r['tool'],
                    'params': r['params'],
                    'description': r['description'],
                    'success': r['success'],
                    'response_time': r['response_time'],
                    'error': r['error'],
                    'result_preview': r['result_preview']
                }
                for r in results['detailed_results']
            ]
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(serializable_results, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Evaluation results saved to {output_path}")
        print(f"\n评估结果已保存到: {output_path}")


# 全局评估器实例
tool_evaluator = ToolCallEvaluator()

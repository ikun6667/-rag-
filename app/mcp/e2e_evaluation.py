"""
端到端工具调用成功率评估 - 基于 Workflow 的自然语言交互测试
测试系统是否能正确理解用户需求、选择合适的工具并成功执行
"""
import asyncio
import json
import time
from typing import List, Dict, Any
from app.graph.workflow import workflow_app
from app.agents.planner_agent import planner_agent
import logging

logger = logging.getLogger(__name__)


class EndToEndToolEvaluator:
    """端到端工具调用评估器"""
    
    def __init__(self):
        self.test_cases = []
    
    def load_test_cases(self, test_cases_path: str = None):
        """
        加载端到端测试用例
        
        Args:
            test_cases_path: 测试用例JSON文件路径，如果为None则使用默认测试集
        """
        if test_cases_path:
            with open(test_cases_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.test_cases = data.get('test_cases', [])
        else:
            # 使用默认端到端测试用例（15个真实场景）
            self.test_cases = [
                {
                    "query": "北京明天的天气怎么样？",
                    "expected_agents": ["weather"],
                    "description": "纯天气查询 - 应该只调用 weather agent"
                },
                {
                    "query": "推荐一些北京的旅游景点",
                    "expected_agents": ["attraction"],
                    "description": "纯景点查询 - 应该只调用 attraction agent"
                },
                {
                    "query": "上海有什么好的酒店推荐？",
                    "expected_agents": ["hotel"],
                    "description": "纯酒店查询 - 应该只调用 hotel agent"
                },
                {
                    "query": "我想去杭州玩3天，帮我规划一下行程",
                    "expected_agents": ["attraction", "weather", "hotel"],
                    "description": "完整旅行规划 - 应该调用所有 agent"
                },
                {
                    "query": "成都的天气和景点推荐",
                    "expected_agents": ["weather", "attraction"],
                    "description": "天气+景点组合查询"
                },
                {
                    "query": "西安有哪些值得去的景点？住宿有什么建议？",
                    "expected_agents": ["attraction", "hotel"],
                    "description": "景点+酒店组合查询"
                },
                {
                    "query": "周末想去上海玩，需要注意什么天气情况？",
                    "expected_agents": ["weather"],
                    "description": "以天气为主的查询"
                },
                {
                    "query": "帮我安排一个北京5日游的行程，预算中等",
                    "expected_agents": ["attraction", "weather", "hotel"],
                    "description": "多日完整行程规划"
                },
                {
                    "query": "广州有什么好吃的餐厅推荐？",
                    "expected_agents": ["attraction"],
                    "description": "餐饮查询（通过 attraction agent 处理）"
                },
                {
                    "query": "深圳下周的天气如何？适合出去玩吗？",
                    "expected_agents": ["weather"],
                    "description": "天气查询+出行建议"
                },
                {
                    "query": "南京有哪些经济实惠的酒店？",
                    "expected_agents": ["hotel"],
                    "description": "预算敏感型酒店查询"
                },
                {
                    "query": "重庆有什么必去的景点和特色美食？",
                    "expected_agents": ["attraction"],
                    "description": "景点+美食综合查询"
                },
                {
                    "query": "计划去厦门旅游3天，帮我看看天气和推荐景点",
                    "expected_agents": ["weather", "attraction"],
                    "description": "短期旅行的天气+景点规划"
                },
                {
                    "query": "青岛的海边酒店推荐，最好能看到海景",
                    "expected_agents": ["hotel"],
                    "description": "特定需求的酒店查询"
                },
                {
                    "query": "我想去云南大理玩一周，帮我做个完整的旅行计划",
                    "expected_agents": ["attraction", "weather", "hotel"],
                    "description": "长期完整旅行规划"
                }
            ]
        
        logger.info(f"Loaded {len(self.test_cases)} end-to-end test cases")
    
    async def test_single_query(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """
        测试单个自然语言查询
        
        Args:
            test_case: 测试用例字典
            
        Returns:
            测试结果字典
        """
        query = test_case['query']
        expected_agents = test_case.get('expected_agents', [])
        description = test_case.get('description', '')
        
        result = {
            'query': query,
            'expected_agents': expected_agents,
            'description': description,
            'success': False,
            'response_time': 0,
            'error': None,
            'actual_agents': [],
            'agent_selection_correct': False,
            'response_preview': None,
            'routing_correct': False
        }
        
        start_time = time.time()
        
        try:
            # 构建初始状态
            initial_state = {
                "query": query,
                "location": self._extract_location(query),
                "days": self._extract_days(query),
                "budget": "中等",
                "preferences": "",
                "attraction_result": {},
                "weather_result": {},
                "hotel_result": {},
                "plan_result": {},
                "next_step": "",
                "needs_clarification": False,
                "clarification_questions": [],
                "agents_to_run": [],
                "completed_agents": [],
                "final_response": ""
            }
            
            # 执行 workflow
            final_state = await workflow_app.ainvoke(initial_state)
            
            end_time = time.time()
            result['response_time'] = end_time - start_time
            
            # 获取实际运行的 agents
            actual_agents = final_state.get('agents_to_run', [])
            result['actual_agents'] = actual_agents
            
            # 检查 agent 选择是否正确
            expected_set = set(expected_agents)
            actual_set = set(actual_agents)
            
            # 判断是否完全匹配（允许实际运行的比预期的多，但不能少）
            agent_selection_correct = expected_set.issubset(actual_set)
            result['agent_selection_correct'] = agent_selection_correct
            
            # 检查是否有最终响应
            final_response = final_state.get('final_response', '')
            routing_correct = len(final_response) > 50  # 简单判断：有合理长度的回复
            
            result['routing_correct'] = routing_correct
            result['success'] = agent_selection_correct and routing_correct
            
            # 保存响应预览
            if final_response:
                result['response_preview'] = final_response[:300]
            
            logger.info(f"✓ Test case succeeded in {result['response_time']:.2f}s")
            
        except Exception as e:
            end_time = time.time()
            result['success'] = False
            result['response_time'] = end_time - start_time
            result['error'] = str(e)
            
            logger.error(f"✗ Test case failed: {e}")
        
        return result
    
    def _extract_location(self, query: str) -> str:
        """从查询中提取地点（简化版）"""
        cities = ['北京', '上海', '广州', '深圳', '杭州', '成都', '重庆', 
                  '西安', '南京', '武汉', '天津', '苏州', '青岛', '大连', 
                  '厦门', '三亚', '昆明', '大理', '丽江', '桂林']
        
        for city in cities:
            if city in query:
                return city
        
        return "北京"  # 默认
    
    def _extract_days(self, query: str) -> int:
        """从查询中提取天数（简化版）"""
        import re
        match = re.search(r'(\d+)\s*天', query)
        if match:
            return int(match.group(1))
        return 3  # 默认
    
    async def evaluate_all(self) -> Dict[str, Any]:
        """
        执行所有端到端测试
        
        Returns:
            评估结果字典
        """
        if not self.test_cases:
            raise ValueError("No test cases loaded. Call load_test_cases first.")
        
        results = []
        success_count = 0
        total_time = 0
        correct_routing_count = 0
        correct_agent_selection_count = 0
        
        print(f"\n{'='*80}")
        print(f"开始端到端工具调用成功率评估（基于 Workflow 自然语言交互）")
        print(f"{'='*80}\n")
        
        for i, test_case in enumerate(self.test_cases, 1):
            print(f"[{i}/{len(self.test_cases)}] 测试: {test_case.get('description', '')}")
            print(f"  用户查询: {test_case['query']}")
            print(f"  期望调用的 Agent: {test_case.get('expected_agents', [])}")
            
            result = await self.test_single_query(test_case)
            results.append(result)
            
            if result['success']:
                success_count += 1
                status = "✓ 成功"
            else:
                status = "✗ 失败"
            
            print(f"  实际调用的 Agent: {result['actual_agents']}")
            print(f"  Agent 选择正确: {'✓' if result['agent_selection_correct'] else '✗'}")
            print(f"  路由正确: {'✓' if result['routing_correct'] else '✗'}")
            print(f"  {status} (耗时: {result['response_time']:.2f}s)")
            
            if result['error']:
                print(f"  错误: {result['error']}")
            
            if result['response_preview']:
                preview = result['response_preview'].replace('\n', ' ')
                print(f"  响应预览: {preview[:100]}...")
            
            if result['agent_selection_correct']:
                correct_agent_selection_count += 1
            if result['routing_correct']:
                correct_routing_count += 1
            
            total_time += result['response_time']
            print()
        
        # 计算统计指标
        success_rate = success_count / len(self.test_cases) * 100 if self.test_cases else 0
        avg_response_time = total_time / len(self.test_cases) if self.test_cases else 0
        agent_selection_accuracy = correct_agent_selection_count / len(self.test_cases) * 100
        routing_accuracy = correct_routing_count / len(self.test_cases) * 100
        
        # 按预期 Agent 分组统计
        scenario_stats = {}
        for result in results:
            expected_key = ','.join(sorted(result['expected_agents']))
            if expected_key not in scenario_stats:
                scenario_stats[expected_key] = {
                    'scenario': result['expected_agents'],
                    'total': 0,
                    'success': 0,
                    'failed': 0,
                    'correct_agent_selection': 0,
                    'correct_routing': 0
                }
            
            scenario_stats[expected_key]['total'] += 1
            if result['success']:
                scenario_stats[expected_key]['success'] += 1
            else:
                scenario_stats[expected_key]['failed'] += 1
            if result['agent_selection_correct']:
                scenario_stats[expected_key]['correct_agent_selection'] += 1
            if result['routing_correct']:
                scenario_stats[expected_key]['correct_routing'] += 1
        
        # 输出总结
        print(f"\n{'='*80}")
        print(f"端到端评估结果总结")
        print(f"{'='*80}")
        print(f"总测试用例数:              {len(self.test_cases)}")
        print(f"完全成功数:                {success_count}")
        print(f"失败数:                    {len(self.test_cases) - success_count}")
        print(f"总体成功率:                {success_rate:.2f}%")
        print(f"Agent 选择准确率:          {agent_selection_accuracy:.2f}%")
        print(f"路由正确率:                {routing_accuracy:.2f}%")
        print(f"平均响应时间:              {avg_response_time:.2f}s")
        print(f"总耗时:                    {total_time:.2f}s")
        
        print(f"\n各场景类型详细统计:")
        print(f"{'-'*80}")
        
        for scenario_key, stats in scenario_stats.items():
            scenario_name = stats['scenario']
            print(f"\n场景: {scenario_name}")
            print(f"  测试次数:              {stats['total']}")
            print(f"  成功次数:              {stats['success']}")
            print(f"  失败次数:              {stats['failed']}")
            print(f"  成功率:                {stats['success']/stats['total']*100:.2f}%")
            print(f"  Agent选择准确率:       {stats['correct_agent_selection']/stats['total']*100:.2f}%")
            print(f"  路由正确率:            {stats['correct_routing']/stats['total']*100:.2f}%")
        
        print(f"\n{'='*80}\n")
        
        return {
            'total_tests': len(self.test_cases),
            'success_count': success_count,
            'failed_count': len(self.test_cases) - success_count,
            'success_rate': success_rate,
            'agent_selection_accuracy': agent_selection_accuracy,
            'routing_accuracy': routing_accuracy,
            'avg_response_time': avg_response_time,
            'total_time': total_time,
            'scenario_statistics': scenario_stats,
            'detailed_results': results
        }
    
    def save_results(self, results: Dict[str, Any], output_path: str = "e2e_tool_evaluation_results.json"):
        """
        保存评估结果到文件
        
        Args:
            results: 评估结果字典
            output_path: 输出文件路径
        """
        serializable_results = {
            'total_tests': results['total_tests'],
            'success_count': results['success_count'],
            'failed_count': results['failed_count'],
            'success_rate': results['success_rate'],
            'agent_selection_accuracy': results['agent_selection_accuracy'],
            'routing_accuracy': results['routing_accuracy'],
            'avg_response_time': results['avg_response_time'],
            'total_time': results['total_time'],
            'scenario_statistics': {
                k: v for k, v in results['scenario_statistics'].items()
            },
            'detailed_results': [
                {
                    'query': r['query'],
                    'expected_agents': r['expected_agents'],
                    'actual_agents': r['actual_agents'],
                    'description': r['description'],
                    'success': r['success'],
                    'agent_selection_correct': r['agent_selection_correct'],
                    'routing_correct': r['routing_correct'],
                    'response_time': r['response_time'],
                    'error': r['error'],
                    'response_preview': r['response_preview']
                }
                for r in results['detailed_results']
            ]
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(serializable_results, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Evaluation results saved to {output_path}")
        print(f"\n评估结果已保存到: {output_path}")


# 全局评估器实例
e2e_evaluator = EndToEndToolEvaluator()

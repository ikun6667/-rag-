"""
Agent 基类
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from app.models.llm_client import llm_client
from app.cache.redis_cache import cache_manager
from pydantic import ValidationError
import asyncio
import logging
import json

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Agent 抽象基类"""
    
    def __init__(self, name: str, cache_enabled: bool = True, tools: List = None, model_tier=None):
        self.name = name
        self.llm = llm_client
        self.cache_enabled = cache_enabled
        self.cache_prefix = f"agent:{name}"
        self.tools = tools or []
        self.model_tier = model_tier  # 模型层级，用于模型路由
        
        # 如果提供了工具，创建带工具绑定的LLM
        if self.tools:
            self.llm_with_tools = self.llm.chat_model.bind_tools(self.tools)
            logger.info(f"{self.name} initialized with {len(self.tools)} tools")
        else:
            self.llm_with_tools = None
    
    @abstractmethod
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行 Agent 任务"""
        pass
    
    def _get_cache_key(self, **kwargs) -> str:
        """生成缓存键"""
        params = "|".join(f"{k}={v}" for k, v in sorted(kwargs.items()))
        return f"{self.cache_prefix}:{params}"
    
    def _get_from_cache(self, key: str) -> Optional[Any]:
        """从缓存获取"""
        if self.cache_enabled:
            return cache_manager.get(key)
        return None
    
    def _set_to_cache(self, key: str, value: Any, ttl: int = None):
        """设置缓存"""
        if self.cache_enabled:
            cache_manager.set(key, value, ttl)
    
    def _create_prompt(self, template: str, **variables) -> str:
        """创建 Prompt"""
        prompt_template = ChatPromptTemplate.from_template(template)
        return prompt_template.format(**variables)
    
    async def _call_llm(self, prompt: str, use_cache: bool = True, 
                       cache_key: str = None, task_type: Optional[str] = None) -> str:
        """
        调用 LLM
        
        Args:
            prompt: 提示词
            use_cache: 是否使用缓存
            cache_key: 缓存键
            task_type: 任务类型，用于模型路由
        """
        # 尝试从缓存获取
        if use_cache and cache_key:
            cached_result = self._get_from_cache(cache_key)
            if cached_result:
                logger.debug(f"Cache hit for {cache_key}")
                return cached_result
        
        # 调用 LLM（支持模型路由）
        result = await self.llm.generate_async(prompt, task_type=task_type)
        
        # 保存到缓存
        if use_cache and cache_key:
            self._set_to_cache(cache_key, result)
        
        return result
    
    async def _call_llm_with_tools(self, messages: list, max_iterations: int = 3) -> str:
        """
        调用带工具的 LLM，支持多轮工具调用
        
        Args:
            messages: 消息列表
            max_iterations: 最大工具调用迭代次数
        
        Returns:
            最终的文字回复
        """
        if not self.llm_with_tools:
            raise ValueError("No tools bound to this agent")
        
        current_messages = messages.copy()
        
        for iteration in range(max_iterations):
            logger.info(f"Tool calling iteration {iteration + 1}")
            
            # 调用 LLM
            response = await self.llm_with_tools.ainvoke(current_messages)
            
            # 检查是否有工具调用
            if hasattr(response, 'tool_calls') and response.tool_calls:
                logger.info(f"LLM wants to call {len(response.tool_calls)} tools")
                
                # 添加工具调用到消息历史
                current_messages.append(response)
                
                # 执行所有工具调用
                for tool_call in response.tool_calls:
                    tool_name = tool_call['name']
                    tool_args = tool_call['args']
                    tool_id = tool_call['id']
                    
                    logger.info(f"Executing tool: {tool_name} with args: {tool_args}")
                    
                    # 查找并执行工具
                    tool_result = await self._execute_tool(tool_name, tool_args)
                    
                    # 添加工具结果到消息历史
                    current_messages.append(
                        ToolMessage(content=tool_result, tool_call_id=tool_id)
                    )
            else:
                # 没有工具调用，返回最终回复
                logger.info("No more tool calls, returning final response")
                return response.content
        
        # 达到最大迭代次数，返回最后的结果
        logger.warning(f"Reached max iterations ({max_iterations})")
        return current_messages[-1].content if current_messages else ""
    
    async def _execute_tool(self, tool_name: str, tool_args: dict, max_retries: int = 2) -> str:
        """
        执行单个工具，带 Pydantic 强校验 + 失败重试
        
        Args:
            tool_name: 工具名称
            tool_args: 工具参数
            max_retries: 校验/执行失败时的最大重试次数，默认 2 次
        
        Returns:
            工具执行结果的字符串表示
        """
        # 查找匹配的工具
        target_tool = None
        for tool in self.tools:
            if tool.name == tool_name:
                target_tool = tool
                break
        
        if not target_tool:
            return json.dumps({"error": f"Tool '{tool_name}' not found"}, ensure_ascii=False)
        
        last_error = None
        for attempt in range(1, max_retries + 2):  # 1次正常 + max_retries次重试
            try:
                # 用 tool 自带的 args_schema 校验参数
                if hasattr(target_tool, 'args_schema') and target_tool.args_schema is not None:
                    validated = target_tool.args_schema(**tool_args)
                    tool_args = validated.model_dump()
                
                # 执行工具
                if hasattr(target_tool, 'coroutine') and target_tool.coroutine is not None:
                    result = await target_tool.coroutine(**tool_args)
                elif hasattr(target_tool, 'func') and target_tool.func is not None:
                    result = target_tool.func(**tool_args)
                else:
                    result = await target_tool(**tool_args)
                
                logger.info(f"Tool [{tool_name}] executed successfully")
                return result
                
            except (ValidationError, Exception) as e:
                last_error = str(e)
                logger.warning(f"Tool [{tool_name}] failed (attempt {attempt}): {e}")
                if attempt <= max_retries:
                    await asyncio.sleep(0.5 * attempt)
                    continue
        
        # 所有重试耗尽
        logger.error(f"Tool [{tool_name}] failed after {max_retries + 1} attempts: {last_error}")
        return json.dumps({"error": f"工具执行失败（已重试{max_retries}次）: {last_error}"}, ensure_ascii=False)
    
    def __repr__(self):
        return f"{self.__class__.__name__}(name={self.name})"

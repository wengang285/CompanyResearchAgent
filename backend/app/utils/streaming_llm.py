"""流式 LLM 调用工具"""
import asyncio
from typing import Callable, Optional
from openai import AsyncOpenAI
from ..config import get_settings

settings = get_settings()


class StreamingLLM:
    """流式 LLM 调用工具"""
    
    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
        )
        self.model = settings.openai_model
    
    async def stream_completion(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        stream_callback: Optional[Callable[[str], None]] = None,
        temperature: float = 0.7,
    ) -> str:
        """
        流式调用 LLM
        
        Args:
            prompt: 用户提示
            system_prompt: 系统提示
            stream_callback: 流式回调函数，每次收到token时调用
            temperature: 温度参数
        
        Returns:
            完整的响应内容
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        full_content = ""
        
        try:
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                stream=True,
            )
            
            async for chunk in stream:
                if chunk.choices and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    if delta and delta.content:
                        content = delta.content
                        full_content += content
                        
                        # 调用流式回调
                        if stream_callback:
                            if asyncio.iscoroutinefunction(stream_callback):
                                await stream_callback(content)
                            else:
                                stream_callback(content)
            
            return full_content
            
        except Exception as e:
            print(f"[StreamingLLM] 流式调用失败: {e}")
            raise
    
    async def stream_completion_with_metadata(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        stream_callback: Optional[Callable[[str, dict], None]] = None,
        temperature: float = 0.7,
    ) -> str:
        """
        流式调用 LLM，带元数据
        
        Args:
            prompt: 用户提示
            system_prompt: 系统提示
            stream_callback: 流式回调函数，接收 (content, metadata)
            temperature: 温度参数
        
        Returns:
            完整的响应内容
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        full_content = ""
        token_count = 0
        
        try:
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                stream=True,
            )
            
            async for chunk in stream:
                if chunk.choices and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    if delta and delta.content:
                        content = delta.content
                        full_content += content
                        token_count += 1
                        
                        # 调用流式回调，带元数据
                        if stream_callback:
                            metadata = {
                                "token_count": token_count,
                                "finished": False,
                            }
                            if asyncio.iscoroutinefunction(stream_callback):
                                await stream_callback(content, metadata)
                            else:
                                stream_callback(content, metadata)
            
            # 发送完成信号
            if stream_callback:
                metadata = {
                    "token_count": token_count,
                    "finished": True,
                }
                if asyncio.iscoroutinefunction(stream_callback):
                    await stream_callback("", metadata)
                else:
                    stream_callback("", metadata)
            
            return full_content
            
        except Exception as e:
            print(f"[StreamingLLM] 流式调用失败: {e}")
            raise


# 全局实例
streaming_llm = StreamingLLM()


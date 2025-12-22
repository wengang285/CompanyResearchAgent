"""WebSocket 连接管理器"""
from typing import List, Dict, Any
from fastapi import WebSocket


class ConnectionManager:
    """WebSocket 连接管理器"""
    
    def __init__(self):
        # 存储活跃的 WebSocket 连接
        # task_connections: {task_id: [websocket, ...]}
        self.task_connections: dict[str, List[WebSocket]] = {}
        # conversation_connections: {conversation_id: [websocket, ...]}
        self.conversation_connections: dict[str, List[WebSocket]] = {}
    
    async def connect(self, task_id: str, websocket: WebSocket):
        """添加任务连接（兼容旧 API）"""
        await websocket.accept()
        if task_id not in self.task_connections:
            self.task_connections[task_id] = []
        self.task_connections[task_id].append(websocket)
    
    async def connect_conversation(self, conversation_id: str, websocket: WebSocket):
        """添加会话连接"""
        await websocket.accept()
        if conversation_id not in self.conversation_connections:
            self.conversation_connections[conversation_id] = []
        self.conversation_connections[conversation_id].append(websocket)
    
    def disconnect(self, task_id: str, websocket: WebSocket):
        """移除任务连接"""
        if task_id in self.task_connections:
            if websocket in self.task_connections[task_id]:
                self.task_connections[task_id].remove(websocket)
            if not self.task_connections[task_id]:
                del self.task_connections[task_id]
    
    def disconnect_conversation(self, conversation_id: str, websocket: WebSocket):
        """移除会话连接"""
        if conversation_id in self.conversation_connections:
            if websocket in self.conversation_connections[conversation_id]:
                self.conversation_connections[conversation_id].remove(websocket)
            if not self.conversation_connections[conversation_id]:
                del self.conversation_connections[conversation_id]
    
    async def broadcast_progress(self, task_id: str, progress_data: dict):
        """广播进度更新到任务连接（兼容旧 API）"""
        if task_id in self.task_connections:
            disconnected = []
            for connection in self.task_connections[task_id]:
                try:
                    await connection.send_json(progress_data)
                except Exception:
                    disconnected.append(connection)
            
            for conn in disconnected:
                self.disconnect(task_id, conn)
    
    async def broadcast_to_conversation(self, conversation_id: str, data: Dict[str, Any]):
        """广播消息到会话连接"""
        if conversation_id in self.conversation_connections:
            disconnected = []
            for connection in self.conversation_connections[conversation_id]:
                try:
                    await connection.send_json(data)
                except Exception:
                    disconnected.append(connection)
            
            for conn in disconnected:
                self.disconnect_conversation(conversation_id, conn)


# 全局连接管理器实例
ws_manager = ConnectionManager()




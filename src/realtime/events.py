"""
事件处理器
处理来自 Realtime API 的各种事件
"""
from loguru import logger
from datetime import datetime


class EventHandler:
    """事件处理器"""

    def __init__(self, ui=None):
        """初始化事件处理器"""
        self.ui = ui  # UI 管理器
        self.events_received = []
        self.current_task_id = 0  # 当前任务 ID
        self.task_mapping = {}  # 事件 ID 到任务 ID 的映射
        logger.info("事件处理器已初始化")

    def on_speech_started(self, data):
        """检测到说话开始"""
        self.current_task_id += 1

        # 记录事件 ID（如果有）
        event_id = data.get("event_id")
        if event_id:
            self.task_mapping[event_id] = self.current_task_id

        if self.ui:
            self.ui.add_task(self.current_task_id)

        logger.info(f"检测到说话开始 - 任务 #{self.current_task_id}")

    def on_speech_stopped(self, data):
        """检测到说话结束"""
        if self.ui and self.current_task_id > 0:
            self.ui.update_task_status(self.current_task_id, "stopped")

        logger.info(f"检测到说话结束 - 任务 #{self.current_task_id}")

    def on_item_created(self, data):
        """对话项创建（包含转写结果）"""
        try:
            item = data.get("item", {})
            if item.get("type") == "message" and item.get("role") == "user":
                content = item.get("content", [])
                if content:
                    text = content[0].get("text", "")
                    if text and self.ui and self.current_task_id > 0:
                        # 设置原文
                        self.ui.set_task_source(self.current_task_id, text)
                        logger.info(f"转写 (任务 #{self.current_task_id}): {text}")
        except Exception as e:
            logger.error(f"处理转写结果时出错: {e}")

    def on_text_delta(self, data):
        """流式翻译（增量）- 暂时不在这里处理"""
        pass

    def on_text_done(self, data):
        """翻译完成"""
        text = data.get("text", "")
        if text and self.ui and self.current_task_id > 0:
            # 获取当前任务的原文（从 UI 的任务列表中）
            source_text = self._get_task_source(self.current_task_id)

            # 完成任务
            self.ui.complete_task(self.current_task_id, source_text, text)
            logger.info(f"翻译完成 (任务 #{self.current_task_id}): {text}")

    def _get_task_source(self, task_id):
        """从 UI 获取任务的原文"""
        if not self.ui:
            return None

        with self.ui.lock:
            for task in self.ui.active_tasks:
                if task["id"] == task_id:
                    return task.get("source_text")
        return None

    def handle_event(self, event_data):
        """
        处理事件

        Args:
            event_data: 事件数据字典
        """
        event_type = event_data.get("type", "unknown")
        self.events_received.append(event_type)

        # 根据事件类型分发
        handlers = {
            "session.created": self.on_session_created,
            "session.updated": self.on_session_updated,
            "input_audio_buffer.speech_started": self.on_speech_started,
            "input_audio_buffer.speech_stopped": self.on_speech_stopped,
            "input_audio_buffer.committed": self.on_audio_committed,
            "conversation.item.created": self.on_item_created,
            "response.text.delta": self.on_text_delta,
            "response.text.done": self.on_text_done,
            "response.done": self.on_response_done,
            "error": self.on_error
        }

        handler = handlers.get(event_type)
        if handler:
            handler(event_data)
        else:
            logger.debug(f"未处理的事件类型: {event_type}")

    def on_session_created(self, data):
        """会话创建"""
        logger.info("✓ 会话已创建")

    def on_session_updated(self, data):
        """会话更新"""
        logger.info("✓ 会话配置已更新")

    def on_speech_started(self, data):
        """检测到说话开始"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"\n[{timestamp}] 🎤 检测到说话...")
        logger.info("检测到说话开始")

    def on_speech_stopped(self, data):
        """检测到说话结束"""
        print("⚙️  处理中...")
        logger.info("检测到说话结束")

    def on_audio_committed(self, data):
        """音频缓冲已提交"""
        logger.debug("音频缓冲已提交")

    def on_item_created(self, data):
        """对话项创建（包含转写结果）"""
        try:
            item = data.get("item", {})
            if item.get("type") == "message" and item.get("role") == "user":
                content = item.get("content", [])
                if content:
                    text = content[0].get("text", "")
                    if text:
                        timestamp = datetime.now().strftime("%H:%M:%S")
                        print(f"[{timestamp}] 📝 原文: {text}")
                        logger.info(f"转写: {text}")
        except Exception as e:
            logger.error(f"处理转写结果时出错: {e}")

    def on_text_delta(self, data):
        """流式翻译（增量）"""
        delta = data.get("delta", "")
        if delta:
            print(delta, end="", flush=True)

    def on_text_done(self, data):
        """翻译完成"""
        text = data.get("text", "")
        if text:
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"\n[{timestamp}] 🌐 译文: {text}")
            print("-" * 60)
            logger.info(f"翻译: {text}")

    def on_response_done(self, data):
        """响应完成"""
        logger.debug("响应完成")

    def on_error(self, data):
        """错误处理"""
        error = data.get("error", {})
        message = error.get("message", "Unknown error")
        logger.error(f"API 错误: {message}")
        print(f"❌ 错误: {message}")
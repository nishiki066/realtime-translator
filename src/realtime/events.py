"""
事件处理器 - 支持并发翻译，修复原文译文匹配
"""
from loguru import logger
from datetime import datetime
import json
import time


class EventHandler:
    """事件处理器"""

    def __init__(self, ui=None):
        """初始化事件处理器"""
        self.ui = ui
        self.events_received = []

        # 任务管理
        self.task_counter = 0
        self.active_tasks = {}
        self.last_task_id = None

        # ID 映射 - 用于正确匹配原文和译文
        self.item_to_task = {}  # item_id → task_id
        self.response_to_task = {}  # response_id → task_id

        logger.info("事件处理器已初始化 (支持并发翻译)")

    def handle_event(self, event_data):
        """处理事件"""
        event_type = event_data.get("type", "unknown")
        self.events_received.append(event_type)

        logger.debug(f"收到事件: {event_type}")

        # 定义所有已知事件
        known_events = [
            "session.created",
            "session.updated",
            "input_audio_buffer.speech_started",
            "input_audio_buffer.speech_stopped",
            "input_audio_buffer.committed",
            "conversation.item.created",
            "conversation.item.input_audio_transcription.completed",
            "response.created",
            "response.output_item.added",
            "response.output_item.done",
            "response.content_part.added",
            "response.content_part.done",
            "response.text.delta",
            "response.text.done",
            "response.done",
            "error"
        ]

        # 记录未知事件
        if event_type not in known_events:
            logger.info(f"⚠️  未知事件 {event_type}")
            logger.debug(f"完整数据: {json.dumps(event_data, indent=2, ensure_ascii=False)}")

        # 事件处理器映射
        handlers = {
            "session.created": self.on_session_created,
            "session.updated": self.on_session_updated,
            "input_audio_buffer.speech_started": self.on_speech_started,
            "input_audio_buffer.speech_stopped": self.on_speech_stopped,
            "input_audio_buffer.committed": self.on_audio_committed,
            "conversation.item.created": self.on_item_created,
            "conversation.item.input_audio_transcription.completed": self.on_transcription_completed,
            "response.created": self.on_response_created,
            "response.output_item.done": self.on_output_item_done,
            "response.text.delta": self.on_text_delta,
            "response.text.done": self.on_text_done,
            "response.done": self.on_response_done,
            "error": self.on_error,
        }

        handler = handlers.get(event_type)
        if handler:
            handler(event_data)

    def create_task(self, trigger_reason):
        """创建新任务"""
        self.task_counter += 1
        task_id = self.task_counter

        self.active_tasks[task_id] = {
            "source": None,
            "translation": None,
            "status": "created",
            "trigger": trigger_reason,
            "timestamp": datetime.now()
        }

        self.last_task_id = task_id
        logger.info(f"创建任务 #{task_id} (触发原因: {trigger_reason})")
        return task_id

    def on_session_created(self, data):
        """会话创建"""
        logger.info("✓ 会话已创建")
        print("✓ 会话已创建")

    def on_session_updated(self, data):
        """会话更新"""
        logger.info("✓ 会话配置已更新")
        print("✓ 会话配置已更新")

    def on_speech_started(self, data):
        """检测到说话开始"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"\n[{timestamp}] 🎤 检测到说话...")
        logger.info("检测到说话开始")

    def on_speech_stopped(self, data):
        """检测到说话结束（VAD 触发）"""
        timestamp = datetime.now().strftime("%H:%M:%S")

        task_id = self.create_task("vad")

        # 记录 event_id 用于关联（如果有）
        event_id = data.get("event_id")
        if event_id:
            logger.debug(f"记录 event {event_id} → 任务 #{task_id}")

        print(f"[{timestamp}] ⏹️  说话结束 (任务 #{task_id})")
        logger.info(f"检测到说话结束 - 创建任务 #{task_id}")

    def on_audio_committed(self, data):
        """音频缓冲已提交"""
        logger.debug("音频缓冲已提交")
        print("    ⚙️  音频已提交，等待处理...")

    def on_response_created(self, data):
        """响应创建 - 关联 response_id 和任务"""
        response_id = data.get("response_id")

        # 关联 response_id 和当前任务
        if response_id and self.last_task_id:
            self.response_to_task[response_id] = self.last_task_id
            logger.debug(f"关联 response {response_id} → 任务 #{self.last_task_id}")

    def on_item_created(self, data):
        """对话项创建 - 关联 item_id 和任务"""
        item = data.get("item", {})
        item_id = item.get("id")
        item_role = item.get("role")

        # 如果是用户消息，关联 item_id 和当前任务
        if item_role == "user" and item_id and self.last_task_id:
            self.item_to_task[item_id] = self.last_task_id
            logger.debug(f"关联 item {item_id} → 任务 #{self.last_task_id}")

    def on_transcription_completed(self, data):
        """
        转写完成 - 获取日语原文
        使用 item_id 找到对应的任务
        """
        timestamp = datetime.now().strftime("%H:%M:%S")

        logger.info(f"收到转写完成事件")
        logger.debug(f"完整数据: {json.dumps(data, indent=2, ensure_ascii=False)}")

        # 获取 item_id 和转写文本
        item_id = data.get("item_id")
        transcript = data.get("transcript", "")

        if not transcript:
            logger.warning("转写事件中没有 transcript 字段")
            return

        # 查找对应的任务 ID
        task_id = self.item_to_task.get(item_id, self.last_task_id)

        if task_id and task_id in self.active_tasks:
            self.active_tasks[task_id]["source"] = transcript
            print(f"[{timestamp}] 📝 原文 (任务 #{task_id}): {transcript}")
            logger.info(f"✓ 保存原文到任务 #{task_id}")
        else:
            # 如果找不到任务，仍然显示原文
            print(f"[{timestamp}] 📝 原文: {transcript}")
            logger.warning(f"未找到对应任务，item_id={item_id}, 使用 last_task_id={self.last_task_id}")

            # 尝试保存到最后的任务
            if self.last_task_id and self.last_task_id in self.active_tasks:
                self.active_tasks[self.last_task_id]["source"] = transcript

    def on_output_item_done(self, data):
        """
        输出项完成 - 用于调试
        """
        logger.debug(f"收到 output_item.done 事件")
        logger.debug(f"完整数据: {json.dumps(data, indent=2, ensure_ascii=False)}")

    def on_text_delta(self, data):
        """流式翻译（增量）"""
        delta = data.get("delta", "")
        if delta:
            print(delta, end="", flush=True)

    def on_text_done(self, data):
        """
        翻译完成
        如果原文还没到，等待一小段时间
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        text = data.get("text", "")

        logger.info(f"收到翻译结果: {text}")

        if not text:
            return

        # 尝试从 response_id 找到对应的任务
        response_id = data.get("response_id")
        task_id = self.response_to_task.get(response_id, self.last_task_id)

        if task_id and task_id in self.active_tasks:
            task = self.active_tasks[task_id]
            task["translation"] = text
            task["status"] = "completed"

            # 如果原文还没到，等待 0.5 秒
            if not task.get("source"):
                logger.debug(f"译文先到，等待原文... (任务 #{task_id})")
                time.sleep(1)  # 等待原文事件

            source = task.get("source") or "[未获取到原文]"
            trigger = task.get("trigger", "unknown")

            print(f"\n[{timestamp}] 🌐 译文 (任务 #{task_id}, {trigger}): {text}")
            print(f"    原文: {source}")
            print("-" * 60)

            logger.info(f"✓ 翻译完成 (任务 #{task_id})")

            # 清理旧任务（保留最近 10 个）
            if len(self.active_tasks) > 10:
                oldest_id = min(self.active_tasks.keys())
                del self.active_tasks[oldest_id]
                logger.debug(f"清理旧任务 #{oldest_id}")
        else:
            # 如果找不到任务，仍然显示翻译
            print(f"\n[{timestamp}] 🌐 译文: {text}")
            print("-" * 60)
            logger.warning(f"未找到对应任务，task_id={task_id}")

    def on_response_done(self, data):
        """响应完成"""
        logger.debug("响应完成")

    def on_error(self, data):
        """错误处理"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        error = data.get("error", {})
        message = error.get("message", "Unknown error")

        print(f"\n[{timestamp}] ❌ API 错误: {message}")
        logger.error(f"API 错误: {message}")
        logger.error(f"完整错误数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
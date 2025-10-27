"""
WebSocket 客户端
负责与 OpenAI Realtime API 通信
"""
import websocket
import json
import threading
import certifi
from loguru import logger


class RealtimeClient:
    """Realtime API 客户端"""

    def __init__(self, api_key, url, event_handler):
        """
        初始化客户端

        Args:
            api_key: OpenAI API key
            url: WebSocket URL
            event_handler: 事件处理器
        """
        self.api_key = api_key
        self.url = url
        self.event_handler = event_handler

        self.ws = None
        self.is_connected = False
        self.ws_thread = None

        logger.info("WebSocket 客户端已初始化")

    def connect(self):
        """建立 WebSocket 连接"""
        if self.is_connected:
            logger.warning("WebSocket 已连接")
            return

        try:
            logger.info(f"正在连接到: {self.url[:50]}...")

            # 创建 WebSocket 连接
            self.ws = websocket.WebSocketApp(
                self.url,
                header={
                    "Authorization": f"Bearer {self.api_key}",
                    "OpenAI-Beta": "realtime=v1"
                },
                on_open=self._on_open,
                on_message=self._on_message,
                on_error=self._on_error,
                on_close=self._on_close
            )

            # 在独立线程中运行（使用 certifi 证书）
            self.ws_thread = threading.Thread(
                target=lambda: self.ws.run_forever(
                    sslopt={"ca_certs": certifi.where()}
                ),
                daemon=True
            )
            self.ws_thread.start()

            # 等待连接建立
            import time
            timeout = 10
            start = time.time()
            while not self.is_connected and time.time() - start < timeout:
                time.sleep(0.1)

            if not self.is_connected:
                raise TimeoutError("连接超时")

            logger.info("✓ WebSocket 连接成功")

        except Exception as e:
            logger.error(f"连接失败: {e}")
            raise

    def _on_open(self, ws):
        """连接建立回调"""
        self.is_connected = True
        logger.info("WebSocket 连接已建立")

    def _on_message(self, ws, message):
        """接收消息回调"""
        try:
            data = json.loads(message)
            event_type = data.get("type", "unknown")

            logger.debug(f"收到事件: {event_type}")

            # 交给事件处理器处理
            if self.event_handler:
                self.event_handler.handle_event(data)

        except json.JSONDecodeError as e:
            logger.error(f"消息解析失败: {e}")
        except Exception as e:
            logger.error(f"处理消息时出错: {e}")

    def _on_error(self, ws, error):
        """错误回调"""
        logger.error(f"WebSocket 错误: {error}")

    def _on_close(self, ws, close_status_code, close_msg):
        """连接关闭回调"""
        self.is_connected = False
        logger.info(f"WebSocket 连接已关闭: {close_status_code} - {close_msg}")

    def send_message(self, message_dict):
        """
        发送消息

        Args:
            message_dict: 要发送的消息字典
        """
        if not self.is_connected:
            logger.warning("WebSocket 未连接，无法发送消息")
            return False

        try:
            message_json = json.dumps(message_dict)
            self.ws.send(message_json)
            logger.debug(f"发送消息: {message_dict.get('type', 'unknown')}")
            return True
        except Exception as e:
            logger.error(f"发送消息失败: {e}")
            return False

    def send_audio(self, audio_base64):
        """
        发送音频数据

        Args:
            audio_base64: base64 编码的音频数据
        """
        message = {
            "type": "input_audio_buffer.append",
            "audio": audio_base64
        }
        return self.send_message(message)

    def configure_session(self, instructions, vad_config):
        """
        配置会话

        Args:
            instructions: 系统指令
            vad_config: VAD 配置
        """
        config = {
            "type": "session.update",
            "session": {
                "modalities": ["text", "audio"],  # 同时支持文本和音频
                "instructions": instructions,
                "input_audio_format": "pcm16",
                "output_audio_format": "pcm16",
                "input_audio_transcription": {  # 强制启用输入音频转写
                    "model": "whisper-1"
                },
                "turn_detection": vad_config
            }
        }

        logger.info("发送会话配置...")
        logger.debug(f"配置内容: {config}")
        return self.send_message(config)

    def commit_audio_buffer(self):
        """
        手动提交音频缓冲区
        用于强制触发转写和翻译，即使没有检测到静音

        Returns:
            bool: 是否成功提交
        """
        message = {
            "type": "input_audio_buffer.commit"
        }
        success = self.send_message(message)

        if success:
            logger.info("✓ 手动提交音频缓冲")

            # 提交后立即创建响应
            self.create_response()

        return success

    def create_response(self):
        """
        创建响应（触发转写和翻译）

        Returns:
            bool: 是否成功创建响应
        """
        message = {
            "type": "response.create",
            "response": {
                "modalities": ["text"]
            }
        }
        success = self.send_message(message)

        if success:
            logger.debug("✓ 创建响应请求")

        return success

    def clear_audio_buffer(self):
        """
        清空音频缓冲区
        用于丢弃未处理的音频（可选功能）

        Returns:
            bool: 是否成功清空
        """
        message = {
            "type": "input_audio_buffer.clear"
        }
        success = self.send_message(message)

        if success:
            logger.info("✓ 清空音频缓冲")

        return success

    def cancel_response(self):
        """
        取消当前正在进行的响应
        用于中断长时间运行的翻译（可选功能）

        Returns:
            bool: 是否成功取消
        """
        message = {
            "type": "response.cancel"
        }
        success = self.send_message(message)

        if success:
            logger.info("✓ 取消当前响应")

        return success

    def disconnect(self):
        """断开连接"""
        logger.info("正在断开 WebSocket 连接...")

        self.is_connected = False

        if self.ws:
            try:
                self.ws.close()
            except Exception as e:
                logger.warning(f"关闭 WebSocket 时出错: {e}")
            finally:
                self.ws = None

        # 等待线程结束
        if self.ws_thread and self.ws_thread.is_alive():
            self.ws_thread.join(timeout=2)

        logger.info("✓ WebSocket 已断开")
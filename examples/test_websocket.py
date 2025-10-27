"""
测试 WebSocket 连接
"""
import sys
import time

sys.path.insert(0, '..')

from src.realtime.client import RealtimeClient
from src.realtime.events import EventHandler
from config.settings import config


def test_websocket():
    """测试 WebSocket 连接"""
    print("=" * 60)
    print("测试 WebSocket 连接")
    print("=" * 60)

    # 创建事件处理器
    event_handler = EventHandler()

    # 创建客户端
    client = RealtimeClient(
        api_key=config.OPENAI_API_KEY,
        url=config.REALTIME_URL,
        event_handler=event_handler
    )

    try:
        # 连接
        print("\n正在连接到 OpenAI Realtime API...")
        client.connect()

        # 配置会话
        print("配置会话...")
        vad_config = {
            "type": "server_vad",
            "threshold": config.VAD_THRESHOLD,
            "silence_duration_ms": config.SILENCE_DURATION_MS,
            "prefix_padding_ms": config.PREFIX_PADDING_MS
        }

        client.configure_session(
            instructions=config.SYSTEM_INSTRUCTIONS,
            vad_config=vad_config
        )

        # 等待一会儿，接收服务器响应
        print("\n等待服务器响应...")
        time.sleep(3)

        # 显示接收到的事件
        print(f"\n接收到的事件: {event_handler.events_received}")

        # 断开连接
        print("\n断开连接...")
        client.disconnect()

        print("\n✓ WebSocket 连接测试通过！")
        return True

    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        client.disconnect()
        return False


if __name__ == "__main__":
    test_websocket()
"""
实时语音翻译器 - 主程序
"""
import sys
import time
from loguru import logger

from config.settings import config
from src.audio.recorder import AudioRecorder
from src.audio.processor import AudioProcessor
from src.realtime.client import RealtimeClient
from src.realtime.events import EventHandler


class RealtimeTranslator:
    """实时翻译器"""

    def __init__(self):
        """初始化翻译器"""
        logger.info("初始化实时翻译器...")

        # 验证配置
        config.validate()

        # 创建各个组件
        self.processor = AudioProcessor()
        self.event_handler = EventHandler()

        self.recorder = AudioRecorder(
            sample_rate=config.SAMPLE_RATE,
            chunk_size=config.CHUNK_SIZE,
            channels=config.CHANNELS
        )

        self.client = RealtimeClient(
            api_key=config.OPENAI_API_KEY,
            url=config.REALTIME_URL,
            event_handler=self.event_handler
        )

        self.is_running = False

        logger.info("✓ 翻译器初始化完成")

    def start(self):
        """启动翻译器"""
        try:
            # 显示欢迎信息
            self._show_banner()

            # 连接到 API
            print("\n正在连接到 OpenAI Realtime API...")
            self.client.connect()
            print("✓ 连接成功！")

            # 配置会话
            print("正在配置翻译会话...")
            vad_config = {
                "type": "server_vad",
                "threshold": config.VAD_THRESHOLD,
                "silence_duration_ms": config.SILENCE_DURATION_MS,
                "prefix_padding_ms": config.PREFIX_PADDING_MS
            }

            self.client.configure_session(
                instructions=config.SYSTEM_INSTRUCTIONS,
                vad_config=vad_config
            )

            # 等待配置完成
            time.sleep(1)
            print("✓ 配置完成！")

            # 开始录音
            print("\n开始录音和翻译...")
            print(f"翻译方向: {config.SOURCE_LANGUAGE} → {config.TARGET_LANGUAGE}")
            print("请对着麦克风说话...")
            print("按 Ctrl+C 停止\n")
            print("=" * 60)

            self.recorder.start()
            self.is_running = True

            # 音频发送循环
            self._audio_send_loop()

        except KeyboardInterrupt:
            print("\n\n正在停止...")
            self.stop()
            print("✓ 已停止")

        except Exception as e:
            logger.error(f"运行出错: {e}")
            print(f"\n❌ 错误: {e}")
            self.stop()
            sys.exit(1)

    def _audio_send_loop(self):
        """音频发送循环"""
        logger.info("音频发送循环已启动")

        chunks_sent = 0

        while self.is_running:
            try:
                # 从录音器获取音频块
                audio_chunk = self.recorder.get_audio_chunk()

                if audio_chunk:
                    # 验证音频
                    if self.processor.validate_audio(audio_chunk):
                        # 编码为 base64
                        audio_base64 = self.processor.pcm_to_base64(audio_chunk)

                        if audio_base64:
                            # 发送到 API
                            self.client.send_audio(audio_base64)
                            chunks_sent += 1

                            if chunks_sent % 100 == 0:
                                logger.debug(f"已发送 {chunks_sent} 个音频块")

                # 短暂休眠，避免 CPU 占用过高
                time.sleep(0.01)

            except Exception as e:
                if self.is_running:
                    logger.error(f"音频发送出错: {e}")

        logger.info(f"音频发送循环已停止，共发送 {chunks_sent} 个音频块")

    def stop(self):
        """停止翻译器"""
        logger.info("停止翻译器...")

        self.is_running = False

        # 停止录音
        self.recorder.stop()

        # 断开连接
        self.client.disconnect()

        logger.info("✓ 翻译器已停止")

    def _show_banner(self):
        """显示欢迎横幅"""
        banner = """
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║           实时语音翻译器 v1.0                              ║
║           Realtime Voice Translator                       ║
║                                                           ║
║           基于 OpenAI Realtime API                        ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
        """
        print(banner)


def main():
    """主函数"""
    # 配置日志
    logger.remove()  # 移除默认处理器
    logger.add(
        sys.stderr,
        level="INFO",
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>"
    )
    logger.add(
        "logs/translator_{time}.log",
        rotation="1 day",
        retention="7 days",
        level="DEBUG"
    )

    # 创建并启动翻译器
    translator = RealtimeTranslator()
    translator.start()


if __name__ == "__main__":
    main()
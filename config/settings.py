"""
配置文件
集中管理所有配置项
"""
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class Config:
    """应用配置"""

    # OpenAI API
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    REALTIME_MODEL = os.getenv("REALTIME_MODEL", "gpt-4o-realtime-preview-2024-10-01")

    # WebSocket URL
    @property
    def REALTIME_URL(self):
        return f"wss://api.openai.com/v1/realtime?model={self.REALTIME_MODEL}"

    # 翻译设置
    SOURCE_LANGUAGE = os.getenv("SOURCE_LANGUAGE", "zh")
    TARGET_LANGUAGE = os.getenv("TARGET_LANGUAGE", "en")

    # 音频设置
    SAMPLE_RATE = int(os.getenv("SAMPLE_RATE", "24000"))
    CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1024"))
    CHANNELS = 1  # 单声道
    FORMAT = "pcm16"

    # VAD 设置
    VAD_THRESHOLD = float(os.getenv("VAD_THRESHOLD", "0.5"))
    SILENCE_DURATION_MS = int(os.getenv("SILENCE_DURATION_MS", "1000"))
    PREFIX_PADDING_MS = 300

    # 系统提示词
    @property
    def SYSTEM_INSTRUCTIONS(self):
        return f"""You are a real-time translator.
- Translate from {self.SOURCE_LANGUAGE} to {self.TARGET_LANGUAGE}
- Only provide the translation, no explanations
- Be natural and preserve the tone
"""

    @classmethod
    def validate(cls):
        """验证配置"""
        if not cls.OPENAI_API_KEY:
            raise ValueError("❌ OPENAI_API_KEY not found in .env file")
        if not cls.OPENAI_API_KEY.startswith("sk-"):
            raise ValueError("❌ Invalid OPENAI_API_KEY format")
        print("✓ 配置验证通过")
        return True


# 创建全局配置实例
config = Config()
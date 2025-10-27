"""
音频处理模块
负责音频编码和格式转换
"""
import base64
from loguru import logger


class AudioProcessor:
    """音频处理器"""

    @staticmethod
    def pcm_to_base64(pcm_data):
        """
        将 PCM 音频转为 base64 编码

        Args:
            pcm_data: PCM 音频字节数据

        Returns:
            str: base64 编码的字符串
        """
        if not pcm_data:
            return None

        try:
            return base64.b64encode(pcm_data).decode('utf-8')
        except Exception as e:
            logger.error(f"音频编码失败: {e}")
            return None

    @staticmethod
    def validate_audio(pcm_data, expected_size=None):
        """
        验证音频数据格式

        Args:
            pcm_data: 音频数据
            expected_size: 期望的数据大小（可选）

        Returns:
            bool: 数据是否有效
        """
        if not pcm_data:
            return False

        if not isinstance(pcm_data, bytes):
            logger.warning(f"音频数据类型错误: {type(pcm_data)}")
            return False

        if expected_size and len(pcm_data) != expected_size:
            logger.warning(f"音频数据大小不匹配: 期望 {expected_size}, 实际 {len(pcm_data)}")
            return False

        return True
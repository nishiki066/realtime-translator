"""
测试配置模块
"""
import sys

sys.path.insert(0, '..')

from config.settings import config


def test_config():
    """测试配置是否正确加载"""
    print("=" * 60)
    print("测试配置模块")
    print("=" * 60)

    # 验证配置
    try:
        config.validate()
    except ValueError as e:
        print(f"配置验证失败: {e}")
        return False

    # 显示配置信息
    print(f"\n✓ API Key: {config.OPENAI_API_KEY[:10]}...{config.OPENAI_API_KEY[-4:]}")
    print(f"✓ 模型: {config.REALTIME_MODEL}")
    print(f"✓ WebSocket URL: {config.REALTIME_URL[:50]}...")
    print(f"✓ 翻译方向: {config.SOURCE_LANGUAGE} → {config.TARGET_LANGUAGE}")
    print(f"✓ 采样率: {config.SAMPLE_RATE} Hz")
    print(f"✓ 块大小: {config.CHUNK_SIZE}")
    print(f"✓ VAD 沉默时长: {config.SILENCE_DURATION_MS} ms")

    print(f"\n系统提示词:")
    print("-" * 60)
    print(config.SYSTEM_INSTRUCTIONS)
    print("-" * 60)

    print("\n✓ 配置模块测试通过！")
    return True


if __name__ == "__main__":
    test_config()
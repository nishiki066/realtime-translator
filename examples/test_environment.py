"""
测试环境配置
检查所有依赖是否正确安装
"""


def test_imports():
    """测试所有必需的库是否可以导入"""
    print("=" * 60)
    print("测试 Python 库导入...")
    print("=" * 60)

    tests = []

    # 测试 websocket
    try:
        import websocket
        print("✓ websocket-client 已安装")
        tests.append(True)
    except ImportError:
        print("✗ websocket-client 未安装")
        tests.append(False)

    # 测试 pyaudio
    try:
        import pyaudio
        print("✓ pyaudio 已安装")
        tests.append(True)
    except ImportError:
        print("✗ pyaudio 未安装")
        tests.append(False)

    # 测试 dotenv
    try:
        from dotenv import load_dotenv
        print("✓ python-dotenv 已安装")
        tests.append(True)
    except ImportError:
        print("✗ python-dotenv 未安装")
        tests.append(False)

    # 测试 loguru
    try:
        from loguru import logger
        print("✓ loguru 已安装")
        tests.append(True)
    except ImportError:
        print("✗ loguru 未安装")
        tests.append(False)

    print("\n" + "=" * 60)
    if all(tests):
        print("✓ 所有依赖已正确安装！")
        return True
    else:
        print("✗ 有依赖未安装，请运行: pip install -r requirements.txt")
        return False


def test_env_file():
    """测试 .env 文件是否存在且配置正确"""
    print("\n" + "=" * 60)
    print("测试环境变量配置...")
    print("=" * 60)

    import os
    from dotenv import load_dotenv

    # 加载 .env 文件
    load_dotenv()

    # 检查 API key
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        print("✗ OPENAI_API_KEY 未设置")
        print("  请在 .env 文件中设置你的 API key")
        return False

    if not api_key.startswith("sk-"):
        print("✗ OPENAI_API_KEY 格式不正确")
        print("  OpenAI API key 应该以 'sk-' 开头")
        return False

    print(f"✓ OPENAI_API_KEY 已设置: {api_key[:10]}...{api_key[-4:]}")

    # 检查其他配置
    model = os.getenv("REALTIME_MODEL")
    print(f"✓ REALTIME_MODEL: {model}")

    source_lang = os.getenv("SOURCE_LANGUAGE")
    target_lang = os.getenv("TARGET_LANGUAGE")
    print(f"✓ 翻译方向: {source_lang} → {target_lang}")

    print("\n" + "=" * 60)
    print("✓ 环境变量配置正确！")
    return True


def test_pyaudio_devices():
    """测试音频设备"""
    print("\n" + "=" * 60)
    print("检测音频设备...")
    print("=" * 60)

    try:
        import pyaudio

        p = pyaudio.PyAudio()
        device_count = p.get_device_count()

        print(f"\n找到 {device_count} 个音频设备：\n")

        input_devices = []
        for i in range(device_count):
            info = p.get_device_info_by_index(i)
            if info['maxInputChannels'] > 0:  # 只显示输入设备
                input_devices.append(i)
                print(f"设备 {i}: {info['name']}")
                print(f"  - 最大输入声道: {info['maxInputChannels']}")
                print(f"  - 默认采样率: {int(info['defaultSampleRate'])} Hz")
                print()

        if not input_devices:
            print("✗ 没有找到输入设备（麦克风）")
            return False

        # 测试默认输入设备
        default_input = p.get_default_input_device_info()
        print(f"✓ 默认输入设备: {default_input['name']}")

        p.terminate()

        print("\n" + "=" * 60)
        print("✓ 音频设备正常！")
        return True

    except Exception as e:
        print(f"\n✗ 音频设备检测失败: {e}")
        print("\n可能的原因：")
        print("1. pyaudio 未正确安装")
        print("2. 没有可用的麦克风")
        print("3. 系统权限问题")
        return False


def main():
    """运行所有测试"""
    print("\n")
    print("╔═══════════════════════════════════════════════╗")
    print("║     实时翻译器 - 环境测试                    ║")
    print("╚═══════════════════════════════════════════════╝")
    print("\n")

    results = []

    # 测试 1：库导入
    results.append(test_imports())

    # 测试 2：环境变量
    if results[0]:
        results.append(test_env_file())

    # 测试 3：音频设备
    if results[0]:
        results.append(test_pyaudio_devices())

    # 总结
    print("\n")
    print("=" * 60)
    print("测试总结")
    print("=" * 60)

    if all(results):
        print("✓ 所有测试通过！环境配置完成！")
        print("\n你可以继续下一步了 🎉")
    else:
        print("✗ 部分测试失败，请解决上述问题后再继续")

    print("=" * 60)
    print("\n")


if __name__ == "__main__":
    main()
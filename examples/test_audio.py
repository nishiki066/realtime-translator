"""
测试音频录制模块
"""
import sys
import time

sys.path.insert(0, '..')

from src.audio.recorder import AudioRecorder
from src.audio.processor import AudioProcessor
from config.settings import config


def test_audio_recording():
    """测试音频录制"""
    print("=" * 60)
    print("测试音频录制模块")
    print("=" * 60)

    # 创建录音器
    recorder = AudioRecorder(
        sample_rate=config.SAMPLE_RATE,
        chunk_size=config.CHUNK_SIZE,
        channels=config.CHANNELS
    )

    # 创建处理器
    processor = AudioProcessor()

    try:
        # 开始录音
        print("\n开始录音...")
        recorder.start()

        # 录制 3 秒
        print("请对着麦克风说话，录制 3 秒...")
        start_time = time.time()
        chunks_received = 0

        while time.time() - start_time < 3:
            chunk = recorder.get_audio_chunk()
            if chunk:
                chunks_received += 1

                # 验证音频数据
                if processor.validate_audio(chunk):
                    # 转换为 base64
                    encoded = processor.pcm_to_base64(chunk)
                    if encoded:
                        print(f"✓ 接收音频块 {chunks_received}: {len(chunk)} bytes → {len(encoded)} chars (base64)")

            time.sleep(0.01)  # 避免 CPU 占用过高

        print(f"\n✓ 录音完成！共接收 {chunks_received} 个音频块")

        # 停止录音
        recorder.stop()

        print("\n✓ 音频模块测试通过！")
        return True

    except KeyboardInterrupt:
        print("\n\n用户中断测试")
        recorder.stop()
        return False

    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        recorder.stop()
        return False


if __name__ == "__main__":
    test_audio_recording()
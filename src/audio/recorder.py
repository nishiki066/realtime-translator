"""
音频录制模块
负责从麦克风捕获音频
"""
import pyaudio
import threading
from queue import Queue
from loguru import logger


class AudioRecorder:
    """音频录制器"""

    def __init__(self, sample_rate=24000, chunk_size=1024, channels=1):
        """
        初始化录音器

        Args:
            sample_rate: 采样率 (Hz)
            chunk_size: 每次读取的帧数
            channels: 声道数 (1=单声道)
        """
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.channels = channels

        self.audio = None
        self.stream = None
        self.audio_queue = Queue()
        self.is_recording = False
        self.record_thread = None

        logger.info(f"初始化录音器: {sample_rate}Hz, {chunk_size} frames, {channels} channel(s)")

    def start(self):
        """开始录音"""
        if self.is_recording:
            logger.warning("录音已经在进行中")
            return

        try:
            # 初始化 PyAudio
            self.audio = pyaudio.PyAudio()

            # 打开音频流
            self.stream = self.audio.open(
                format=pyaudio.paInt16,  # 16-bit PCM
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size
            )

            self.is_recording = True

            # 启动录音线程
            self.record_thread = threading.Thread(target=self._record_loop, daemon=True)
            self.record_thread.start()

            logger.info("✓ 录音已启动")

        except Exception as e:
            logger.error(f"启动录音失败: {e}")
            self.stop()
            raise

    def _record_loop(self):
        """录音循环（在独立线程中运行）"""
        logger.info("录音线程已启动")

        while self.is_recording:
            try:
                # 读取音频数据
                data = self.stream.read(self.chunk_size, exception_on_overflow=False)

                # 放入队列
                self.audio_queue.put(data)

            except Exception as e:
                if self.is_recording:  # 只在仍在录音时记录错误
                    logger.error(f"录音出错: {e}")
                break

        logger.info("录音线程已停止")

    def get_audio_chunk(self):
        """
        从队列获取音频数据

        Returns:
            bytes: 音频数据，如果队列为空返回 None
        """
        if not self.audio_queue.empty():
            return self.audio_queue.get()
        return None

    def stop(self):
        """停止录音"""
        logger.info("正在停止录音...")

        self.is_recording = False

        # 等待录音线程结束
        if self.record_thread and self.record_thread.is_alive():
            self.record_thread.join(timeout=2)

        # 关闭音频流
        if self.stream:
            try:
                self.stream.stop_stream()
                self.stream.close()
            except Exception as e:
                logger.warning(f"关闭音频流时出错: {e}")
            finally:
                self.stream = None

        # 终止 PyAudio
        if self.audio:
            try:
                self.audio.terminate()
            except Exception as e:
                logger.warning(f"终止 PyAudio 时出错: {e}")
            finally:
                self.audio = None

        # 清空队列
        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
            except:
                break

        logger.info("✓ 录音已停止")

    def __del__(self):
        """析构函数，确保资源被释放"""
        self.stop()
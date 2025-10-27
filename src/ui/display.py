"""
终端 UI 显示模块
使用 Rich 实现左右分栏实时显示
"""
from rich.layout import Layout
from rich.panel import Panel
from rich.console import Console
from rich.live import Live
from rich.text import Text
from datetime import datetime
from threading import Lock


class TranslatorUI:
    """翻译器终端界面"""

    def __init__(self):
        self.console = Console()
        self.layout = Layout()

        # 数据存储
        self.active_tasks = []  # 当前正在处理的任务
        self.history = []  # 历史翻译记录
        self.lock = Lock()  # 线程锁

        # 创建布局
        self._setup_layout()

        # Live 显示对象
        self.live = None

    def _setup_layout(self):
        """设置布局：左右分栏"""
        self.layout.split_row(
            Layout(name="status", ratio=1),
            Layout(name="results", ratio=2)
        )

    def start(self):
        """启动实时显示"""
        self.live = Live(
            self.layout,
            console=self.console,
            refresh_per_second=4,  # 每秒刷新4次
            screen=True
        )
        self.live.start()

    def stop(self):
        """停止显示"""
        if self.live:
            self.live.stop()

    def add_task(self, task_id):
        """添加新任务到状态区"""
        with self.lock:
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.active_tasks.append({
                "id": task_id,
                "timestamp": timestamp,
                "status": "detected",  # detected, stopped, processing, done
                "source_text": None,
                "translation": None
            })
            self._update_display()

    def update_task_status(self, task_id, status):
        """更新任务状态"""
        with self.lock:
            for task in self.active_tasks:
                if task["id"] == task_id:
                    task["status"] = status
                    break
            self._update_display()

    def set_task_source(self, task_id, text):
        """设置任务的原文"""
        with self.lock:
            for task in self.active_tasks:
                if task["id"] == task_id:
                    task["source_text"] = text
                    break
            self._update_display()

    def complete_task(self, task_id, source_text, translation):
        """完成任务，移到历史记录"""
        with self.lock:
            # 从活动任务中移除
            task_to_remove = None
            for task in self.active_tasks:
                if task["id"] == task_id:
                    task_to_remove = task
                    break

            if task_to_remove:
                self.active_tasks.remove(task_to_remove)

                # 添加到历史记录
                self.history.append({
                    "timestamp": task_to_remove["timestamp"],
                    "source": source_text or task_to_remove["source_text"],
                    "translation": translation
                })

            self._update_display()

    def _update_display(self):
        """更新显示内容"""
        if not self.live:
            return

        # 更新左侧状态区
        self.layout["status"].update(self._render_status())

        # 更新右侧结果区
        self.layout["results"].update(self._render_results())

    def _render_status(self):
        """渲染状态区"""
        if not self.active_tasks:
            content = Text("等待语音输入...\n", style="dim")
        else:
            content = Text()
            for i, task in enumerate(self.active_tasks, 1):
                status_icon = {
                    "detected": "🎤",
                    "stopped": "⏹️ ",
                    "processing": "⚙️ ",
                    "done": "✅"
                }.get(task["status"], "❓")

                status_text = {
                    "detected": "检测到说话",
                    "stopped": "说话结束",
                    "processing": "正在处理",
                    "done": "处理完成"
                }.get(task["status"], "未知状态")

                content.append(f"{status_icon} 任务 #{task['id']} - {status_text}\n")
                content.append(f"   时间: {task['timestamp']}\n", style="dim")

                if i < len(self.active_tasks):
                    content.append("\n")

        return Panel(
            content,
            title="[bold cyan]状态监控[/bold cyan]",
            border_style="cyan"
        )

    def _render_results(self):
        """渲染结果区"""
        if not self.history:
            content = Text("暂无翻译结果", style="dim italic")
        else:
            content = Text()

            # 显示最近的记录（从新到旧）
            for record in reversed(self.history[-20:]):  # 最多显示最近20条
                content.append(f"[{record['timestamp']}]\n", style="bold yellow")
                content.append(f"📝 原文: {record['source']}\n", style="green")
                content.append(f"🌐 译文: {record['translation']}\n", style="cyan")
                content.append("─" * 50 + "\n", style="dim")

        return Panel(
            content,
            title=f"[bold green]翻译结果[/bold green] (共 {len(self.history)} 条)",
            border_style="green"
        )
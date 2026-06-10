import sys
import os
import json
import random
from PyQt5.QtWidgets import QApplication, QLabel, QMenu, QMessageBox, QWidget
from PyQt5.QtGui import QMovie
from PyQt5.QtCore import Qt, QPoint


def resource_path(relative_path):
    # PyInstaller 解包后会把资源放到临时目录 _MEIPASS 中。
    base_path = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


def get_config_path():
    """配置文件保存在 exe 同级目录下"""
    if getattr(sys, "frozen", False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "pet_config.json")


gif_path = resource_path(os.path.join("assets", "eat_watermelon.gif"))
config_path = get_config_path()

class PetWindow(QWidget):
    def __init__(self, gif):
        super().__init__(None, Qt.Tool)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_QuitOnClose)  # 窗口关闭时退出应用
        self.label = QLabel(self)
        self.label.setAttribute(Qt.WA_TranslucentBackground)
        self.label.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.drag_offset = QPoint()
        self.dragging = False
        self._menu = None  # 防止菜单被垃圾回收
        self.dialog_lines = [
            "菲比啾比来陪你摸鱼啦。",
            "今天也要开心吃瓜。",
            "别太累了，记得休息一下。",
            "工作再忙，也要看看我。",
        ]
        
        # 检查 GIF 文件是否存在
        if not os.path.exists(gif):
            print(f"错误：GIF 文件不存在 -> {gif}")
            sys.exit(1)
        print(f"加载 GIF: {gif}")
        
        self.movie = QMovie(gif)
        if self.movie.isValid():
            print(f"GIF 有效，帧数: {self.movie.frameCount()}")
        else:
            print("错误：GIF 加载失败或格式不支持")
            sys.exit(1)
            
        self.label.setMovie(self.movie)
        self.movie.setCacheMode(QMovie.CacheAll)
        self.movie.setSpeed(100)  # 速度 100%，可调
        self.movie.start()
        self.movie.jumpToFrame(0)
        
        # 设置窗口大小（使用 GIF 第一帧）
        size = self.movie.currentPixmap().size()
        if not size.isValid() or size.width() <= 0 or size.height() <= 0:
            size = self.movie.frameRect().size()
        if size.isValid() and size.width() > 0 and size.height() > 0:
            self.setFixedSize(size)
            self.label.setFixedSize(size)
            print(f"窗口大小: {size.width()} x {size.height()}")
        else:
            print("错误：无法获取 GIF 原始尺寸")
            sys.exit(1)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.drag_offset = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()
            return
        if event.button() == Qt.RightButton:
            self.show_context_menu(event.globalPos())
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.dragging and event.buttons() & Qt.LeftButton:
            self.move(event.globalPos() - self.drag_offset)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = False
            self.save_position()  # 拖拽结束后即时保存位置
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def show_context_menu(self, global_pos):
        self._menu = QMenu(self)
        dialog_action = self._menu.addAction("对话")
        eat_action = self._menu.addAction("吃瓜")
        self._menu.addAction("退出")

        # 用信号连接，popup() 是非阻塞的，不会暂停动画
        dialog_action.triggered.connect(self.show_dialog)
        eat_action.triggered.connect(self.eat_watermelon)
        self._menu.actions()[2].triggered.connect(self.close)
        self._menu.popup(global_pos)

    def show_dialog(self):
        QMessageBox.information(self, "菲比啾比", random.choice(self.dialog_lines))

    def eat_watermelon(self):
        QMessageBox.information(self, "菲比啾比", "菲比啾比正在开心吃瓜！")

    def save_position(self):
        pos = self.pos()
        try:
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump({"x": pos.x(), "y": pos.y()}, f)
        except Exception as e:
            print(f"保存位置失败: {e}")

    def load_position(self):
        try:
            if os.path.exists(config_path):
                with open(config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data.get("x"), data.get("y")
        except Exception as e:
            print(f"读取位置失败: {e}")
        return None

    def closeEvent(self, event):
        self.save_position()
        super().closeEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = PetWindow(gif_path)
    screen = app.primaryScreen().availableGeometry()

    # 优先读取上次保存的位置，否则使用默认右下角
    saved = win.load_position()
    if saved and saved[0] is not None and saved[1] is not None:
        x, y = saved
        print(f"使用上次保存的位置: ({x}, {y})")
    else:
        x = screen.right() - win.width() - 50
        y = screen.bottom() - win.height() - 80
        print(f"使用默认位置: ({x}, {y})")

    win.move(x, y)
    win.show()
    print("桌宠已启动，按 Ctrl+C 或关闭窗口退出")
    sys.exit(app.exec_())

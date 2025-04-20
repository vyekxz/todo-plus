# MIT License
#
# Copyright (c) 2025 vyekxz
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# Version: public.0.0.1-alpha
# Creator: vyekxz
# Github: https://github.com/vyekxz
# Contact: vyekxz@gmail.com
# License: © 2025 vyekxz. Released under the MIT License.

import sys
import ctypes
import json
import os
from ctypes import wintypes
from PyQt5.QtWidgets import (
    QApplication, QWidget, QListWidget, QVBoxLayout, QLineEdit,
    QListWidgetItem, QAbstractItemView, QLabel, QPushButton, QTextEdit,
    QScrollArea, QSpinBox
)
from PyQt5.QtCore import Qt, QTimer, QRect, QPropertyAnimation, QEasingCurve, QObject, pyqtSignal
from PyQt5.QtGui import QColor, QPainter, QBrush, QRadialGradient, QFontDatabase, QFont, QIcon

class ACCENTPOLICY(ctypes.Structure):
    _fields_ = [('AccentState', ctypes.c_int),
                ('AccentFlags', ctypes.c_int),
                ('GradientColor', ctypes.c_int),
                ('AnimationId', ctypes.c_int)]

class WINCOMPATTRDATA(ctypes.Structure):
    _fields_ = [('Attribute', ctypes.c_int),
                ('Data', ctypes.POINTER(ACCENTPOLICY)),
                ('SizeOfData', ctypes.c_size_t)]

def enable_blur(hwnd):
    accent = ACCENTPOLICY()
    accent.AccentState = 3
    accent.GradientColor = 0xCCFFFFFF
    data = WINCOMPATTRDATA()
    data.Attribute = 19
    data.Data = ctypes.pointer(accent)
    data.SizeOfData = ctypes.sizeof(accent)
    ctypes.windll.user32.SetWindowCompositionAttribute(hwnd, ctypes.byref(data))

class ClickableListWidget(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.unfocus_callback = None

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        if self.unfocus_callback:
            self.unfocus_callback()

class GlassyToDo(QWidget):
    def __init__(self, switch_callback):
        super().__init__()
        self.switch_callback = switch_callback
        self.todo_file = "todo_list.json"
        self.settings_file = "settings.json"
        font_id = QFontDatabase.addApplicationFont("font.otf")
        self.font_family = QFontDatabase.applicationFontFamilies(font_id)[0] if font_id != -1 else "Arial"
        self.font_size = 12
        self.load_settings()
        QApplication.setFont(QFont(self.font_family, self.font_size))
        self.init_ui()
        self.load_items()

    def init_ui(self):
        self.setFixedSize(400, 600)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet(f"""
            QWidget {{ background-color: rgba(255, 255, 255, 0.15); color: white;
                       font-family: '{self.font_family}', Arial; font-size: {self.font_size}px; border-radius: 24px; }}
            QListWidget {{ background-color: rgba(255, 255, 255, 0.1); border: none; padding: 8px; border-radius: 16px; }}
            QListWidget::item:selected:active {{ background-color: rgba(255, 255, 255, 0.2); }}
            QLineEdit {{ background-color: rgba(255, 255, 255, 0.1); border: none; border-radius: 14px; padding: 10px; color: white; font-size: {self.font_size - 2}px; }}
        """)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(15, 15, 15, 15)
        self.layout.setSpacing(10)
        self.input = QLineEdit()
        self.input.setPlaceholderText("Add new task and press Enter")
        self.input.returnPressed.connect(self.add_item)
        self.layout.addWidget(self.input)
        self.list_widget = ClickableListWidget()
        self.list_widget.unfocus_callback = self.unfocus_input
        self.list_widget.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.list_widget.setDragDropMode(QAbstractItemView.InternalMove)
        self.list_widget.setDragEnabled(True)
        self.list_widget.setAcceptDrops(True)
        self.list_widget.setFocusPolicy(Qt.NoFocus)
        self.layout.addWidget(self.list_widget)
        QTimer.singleShot(0, self.position_window_bottom_right)

    def position_window_bottom_right(self):
        screen_geometry = QApplication.primaryScreen().availableGeometry()
        x, y = screen_geometry.width() - self.width() - 20, screen_geometry.height() - self.height() - 20
        self.move(x, y)

    def moveEvent(self, event):
        super().moveEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)

    def unfocus_input(self):
        self.input.clearFocus()

    def add_item(self):
        text = self.input.text().strip()
        if text:
            item = QListWidgetItem(text)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsDragEnabled | Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            item.setCheckState(Qt.Unchecked)
            self.list_widget.addItem(item)
            self.input.clear()
            self.save_items()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Backspace:
            for item in self.list_widget.selectedItems():
                self.list_widget.takeItem(self.list_widget.row(item))
            self.save_items()
        elif event.key() in (Qt.Key_Space, Qt.Key_Return, Qt.Key_Enter):
            for item in self.list_widget.selectedItems():
                item.setCheckState(Qt.Checked if item.checkState() == Qt.Unchecked else Qt.Unchecked)
            self.save_items()
        elif event.key() == Qt.Key_Escape:
            self.input.setFocus()

    def save_items(self):
        items = [{"text": self.list_widget.item(i).text(), "checked": self.list_widget.item(i).checkState() == Qt.Checked}
                 for i in range(self.list_widget.count())]
        with open(self.todo_file, "w", encoding="utf-8") as f:
            json.dump(items, f, indent=2, ensure_ascii=False)

    def load_items(self):
        if not os.path.exists(self.todo_file):
            return
        with open(self.todo_file, "r", encoding="utf-8") as f:
            try:
                items = json.load(f)
                for obj in items:
                    item = QListWidgetItem(obj["text"])
                    item.setFlags(item.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsDragEnabled |
                                  Qt.ItemIsEnabled | Qt.ItemIsSelectable)
                    item.setCheckState(Qt.Checked if obj["checked"] else Qt.Unchecked)
                    self.list_widget.addItem(item)
            except Exception as e:
                print("Error loading tasks:", e)

    def load_settings(self):
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.font_size = data.get("font_size", 12)
            except:
                self.font_size = 12

class ExplanationWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedSize(400, 600)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("QWidget { background-color: rgba(255, 255, 255, 0.15); color: white; font-size: 16px; border-radius: 24px; }"
                           "QLabel { color: white; padding: 14px; font-size: 15px; }")
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.text = QLabel("Welcome to the app!\n\nWith this tool you can manage tasks.\n\n• ALT + B: To-do\n• ALT + H: Help\n• ALT + D: Settings\n• ALT + E: Exit\n\nCreate, sort, mark, and delete tasks easily.\n\nCreated by vyekxz")
        self.text.setWordWrap(True)
        self.layout.addWidget(self.text)
        QTimer.singleShot(0, self.position_window_bottom_right)

    def position_window_bottom_right(self):
        screen_geometry = QApplication.primaryScreen().availableGeometry()
        x, y = screen_geometry.width() - self.width() - 20, screen_geometry.height() - self.height() - 20
        self.move(x, y)

class SettingsWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.settings_file = "settings.json"
        self.setFixedSize(400, 600)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("QWidget { background-color: rgba(255, 255, 255, 0.15); color: white; font-size: 18px; border-radius: 24px; }"
                           "QSpinBox { background-color: rgba(255,255,255,0.2); border-radius: 10px; padding: 6px; font-size: 16px; color: white; }")
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.font_size_spinner = QSpinBox()
        self.font_size_spinner.setMinimum(8)
        self.font_size_spinner.setMaximum(48)
        self.font_size_spinner.setValue(self.load_font_size())
        self.font_size_spinner.valueChanged.connect(self.save_font_size)
        self.layout.addWidget(QLabel("Set font size:"))
        self.layout.addWidget(self.font_size_spinner)
        QTimer.singleShot(0, self.position_window_bottom_right)

    def position_window_bottom_right(self):
        screen_geometry = QApplication.primaryScreen().availableGeometry()
        x, y = screen_geometry.width() - self.width() - 20, screen_geometry.height() - self.height() - 20
        self.move(x, y)

    def load_font_size(self):
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get("font_size", 12)
            except:
                return 12
        return 12

    def save_font_size(self):
        data = {"font_size": self.font_size_spinner.value()}
        with open(self.settings_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

class KeyFilter(QObject):
    switchToExplanation = pyqtSignal()
    switchToTodo = pyqtSignal()
    switchToSettings = pyqtSignal()
    exitApp = pyqtSignal()

    def eventFilter(self, obj, event):
        if event.type() == event.KeyPress:
            if event.key() == Qt.Key_H and event.modifiers() & Qt.AltModifier:
                self.switchToExplanation.emit()
                return True
            if event.key() == Qt.Key_B and event.modifiers() & Qt.AltModifier:
                self.switchToTodo.emit()
                return True
            if event.key() == Qt.Key_D and event.modifiers() & Qt.AltModifier:
                self.switchToSettings.emit()
                return True
            if event.key() == Qt.Key_E and event.modifiers() & Qt.AltModifier:
                self.exitApp.emit()
                return True
        return False

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    key_filter = KeyFilter()
    todo_window = GlassyToDo(lambda: None)
    explain_window = ExplanationWindow()
    settings_window = SettingsWindow()

    def show_todo():
        explain_window.hide()
        settings_window.hide()
        todo_window.show()
        enable_blur(int(todo_window.winId()))

    def show_explanation():
        todo_window.hide()
        settings_window.hide()
        explain_window.show()
        enable_blur(int(explain_window.winId()))

    def show_settings():
        todo_window.hide()
        explain_window.hide()
        settings_window.show()
        enable_blur(int(settings_window.winId()))

    def exit_app():
        sys.exit()

    key_filter.switchToExplanation.connect(show_explanation)
    key_filter.switchToTodo.connect(show_todo)
    key_filter.switchToSettings.connect(show_settings)
    key_filter.exitApp.connect(exit_app)

    app.installEventFilter(key_filter)
    todo_window.show()
    enable_blur(int(todo_window.winId()))
    sys.exit(app.exec_())

import sys
import os
import platform
import traceback

# Настройка путей для Qt перед импортом PyQt5
if platform.system() == "Windows":
    # Путь к плагинам в виртуальном окружении
    venv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'venv')
    if os.path.exists(venv_path):
        plugin_path = os.path.join(venv_path, 'Lib', 'site-packages', 'PyQt5', 'Qt', 'plugins')
        if os.path.exists(plugin_path):
            os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = plugin_path
            print(f"Установлен путь к плагинам: {plugin_path}")
        else:
            # Альтернативный путь
            plugin_path = os.path.join(venv_path, 'Lib', 'site-packages', 'PyQt5', 'Qt5', 'plugins')
            if os.path.exists(plugin_path):
                os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = plugin_path
                print(f"Установлен путь к плагинам: {plugin_path}")
            else:
                print("Предупреждение: Не удалось найти путь к плагинам Qt в venv")

try:
    from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                                 QHBoxLayout, QPushButton, QLabel, QScrollArea, 
                                 QSplitter, QFrame, QSizePolicy, QFileDialog)
    from PyQt5.QtCore import Qt, pyqtSignal
    from PyQt5.QtGui import QPixmap, QImage
    import fitz
except ImportError as e:
    print(f"Ошибка импорта: {e}")
    print("Убедитесь, что активировано виртуальное окружение и установлены зависимости:")
    print("venv\\Scripts\\activate")
    print("pip install PyQt5 PyMuPDF")
    input("Нажмите Enter для выхода...")
    sys.exit(1)

class ThumbnailWidget(QWidget):
    """Виджет для отображения миниатюр страниц"""
    pageClicked = pyqtSignal(int)
    
    def __init__(self, doc_path):
        super().__init__()
        self.doc_path = doc_path
        self.doc = fitz.open(doc_path)
        self.current_page = 0
        self.thumbnails = []
        self.init_ui()
        self.load_thumbnails()
        
    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        self.scroll_area = QScrollArea()
        self.scroll_widget = QWidget()
        self.thumb_layout = QVBoxLayout(self.scroll_widget)
        self.scroll_area.setWidget(self.scroll_widget)
        self.scroll_area.setWidgetResizable(True)
        
        layout.addWidget(self.scroll_area)
        
    def load_thumbnails(self):
        """Загружает миниатюры всех страниц"""
        for i in range(len(self.doc)):
            try:
                page = self.doc.load_page(i)
                pix = page.get_pixmap(matrix=fitz.Matrix(0.2, 0.2))
                
                img_data = pix.tobytes("ppm")
                qimage = QImage()
                qimage.loadFromData(img_data, "PPM")
                pixmap = QPixmap.fromImage(qimage)
                
                thumb_frame = QFrame()
                thumb_frame.setFrameStyle(QFrame.Box)
                thumb_frame.setLineWidth(2)
                thumb_frame.setFixedHeight(150)
                thumb_layout = QVBoxLayout(thumb_frame)
                
                thumb_label = QLabel()
                thumb_label.setPixmap(pixmap)
                thumb_label.setAlignment(Qt.AlignCenter)
                thumb_label.mousePressEvent = lambda event, page_num=i: self.on_thumbnail_click(page_num)
                
                page_label = QLabel(f"Страница {i+1}")
                page_label.setAlignment(Qt.AlignCenter)
                
                thumb_layout.addWidget(thumb_label)
                thumb_layout.addWidget(page_label)
                
                self.thumb_layout.addWidget(thumb_frame)
                self.thumbnails.append(thumb_frame)
                
            except Exception as e:
                print(f"Ошибка загрузки миниатюры страницы {i}: {e}")
            
        self.highlight_current_page()
    
    def on_thumbnail_click(self, page_num):
        """Обработчик клика по миниатюре"""
        self.pageClicked.emit(page_num)
    
    def highlight_current_page(self):
        """Подсвечивает текущую страницу"""
        for i, thumb in enumerate(self.thumbnails):
            if i == self.current_page:
                thumb.setStyleSheet("background-color: lightblue; border: 2px solid blue;")
            else:
                thumb.setStyleSheet("background-color: white; border: 1px solid gray;")
    
    def set_current_page(self, page_num):
        """Устанавливает текущую страницу"""
        self.current_page = page_num
        self.highlight_current_page()

class PDFViewer(QMainWindow):
    def __init__(self, pdf_path):
        super().__init__()
        self.pdf_path = pdf_path
        self.doc = fitz.open(pdf_path)
        self.current_page = 0
        self.total_pages = len(self.doc)
        
        self.presenter_window = None
        self.photo = None  # Для хранения ссылки на изображение
        
        self.init_ui()
        self.load_page(0)
        
    def init_ui(self):
        self.setWindowTitle(f"PDF Reader - {os.path.basename(self.pdf_path)}")
        self.setGeometry(100, 100, 1200, 800)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        splitter = QSplitter(Qt.Horizontal)
        
        # Левая панель - просмотр PDF
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        self.pdf_label = QLabel()
        self.pdf_label.setAlignment(Qt.AlignCenter)
        self.pdf_label.setStyleSheet("border: 1px solid gray; background-color: white;")
        self.pdf_label.setMinimumSize(400, 200)
        self.pdf_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.pdf_label.setScaledContents(False)  # Важно: отключаем автоматическое масштабирование
        
        scroll_area = QScrollArea()
        scroll_area.setWidget(self.pdf_label)
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        left_layout.addWidget(scroll_area)
        
        # Панель управления
        control_panel = self.create_control_panel()
        left_layout.addWidget(control_panel)
        
        # Правая панель - миниатюры
        self.thumbnail_widget = ThumbnailWidget(self.pdf_path)
        self.thumbnail_widget.pageClicked.connect(self.on_thumbnail_click)
        self.thumbnail_widget.setMaximumWidth(350)
        
        splitter.addWidget(left_panel)
        splitter.addWidget(self.thumbnail_widget)
        splitter.setSizes([400, 200])
        
        main_layout.addWidget(splitter)
        
        # Создаем второе окно для режима докладчика
        self.create_presenter_window()
        
    def create_control_panel(self):
        """Создает панель управления"""
        panel = QWidget()
        layout = QHBoxLayout(panel)
        
        # Кнопка "Предыдущая"
        self.prev_btn = QPushButton("← Пред.")
        self.prev_btn.clicked.connect(self.previous_page)
        self.prev_btn.setMinimumHeight(35)
        
        # Информация о странице
        self.page_info = QLabel()
        self.page_info.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.update_page_info()
        
        # Кнопка "Следующая"
        self.next_btn = QPushButton("След. →")
        self.next_btn.clicked.connect(self.next_page)
        self.next_btn.setMinimumHeight(35)
        
        # Кнопка режима докладчика
        self.presenter_btn = QPushButton("📺 Режим докладчика")
        self.presenter_btn.clicked.connect(self.toggle_presenter_mode)
        self.presenter_btn.setMinimumHeight(35)
        
        layout.addWidget(self.prev_btn)
        layout.addWidget(self.page_info)
        layout.addWidget(self.next_btn)
        layout.addStretch()
        layout.addWidget(self.presenter_btn)
        
        return panel
    
    def create_presenter_window(self):
        """Создает второе окно для режима докладчика"""
        self.presenter_window = QMainWindow()
        self.presenter_window.setWindowTitle(f"Режим докладчика - {os.path.basename(self.pdf_path)}")
        self.presenter_window.setGeometry(1300, 100, 900, 700)
        
        central_widget = QWidget()
        central_widget.setStyleSheet("background-color: black;")  # Черный фон вокруг слайда
        self.presenter_window.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)  # Убираем отступы
        layout.setSpacing(0)
        
        # Область отображения PDF - занимает всё окно
        self.presenter_label = QLabel()
        self.presenter_label.setAlignment(Qt.AlignCenter)
        self.presenter_label.setStyleSheet("background-color: black;")  # Черный фон
        self.presenter_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.presenter_label.setScaledContents(False)  # Важно: отключаем автоматическое масштабирование
        
        layout.addWidget(self.presenter_label)
        
        # Добавляем обработчик изменения размера для окна докладчика
        self.presenter_window.resizeEvent = self.presenter_resize_event
        
    def presenter_resize_event(self, event):
        """Обработчик изменения размера окна докладчика"""
        # Вызываем родительский метод
        QMainWindow.resizeEvent(self.presenter_window, event)
        # Перерисовываем изображение
        if hasattr(self, 'current_page'):
            self.load_page(self.current_page)
    
    def get_scaled_pixmap(self, pixmap, max_width, max_height):
        """Масштабирует pixmap с сохранением пропорций для вписывания в заданные размеры"""
        original_size = pixmap.size()
        original_width = original_size.width()
        original_height = original_size.height()
        
        # Если изображение меньше максимальных размеров, возвращаем оригинал
        if original_width <= max_width and original_height <= max_height:
            return pixmap
        
        # Вычисляем коэффициенты масштабирования
        width_ratio = max_width / original_width
        height_ratio = max_height / original_height
        
        # Используем меньший коэффициент, чтобы изображение полностью вписалось
        scale_factor = min(width_ratio, height_ratio)
        
        # Вычисляем новые размеры
        new_width = int(original_width * scale_factor)
        new_height = int(original_height * scale_factor)
        
        # Масштабируем изображение
        scaled_pixmap = pixmap.scaled(
            new_width, 
            new_height, 
            Qt.KeepAspectRatio, 
            Qt.SmoothTransformation
        )
        
        return scaled_pixmap
    
    def get_presenter_scaled_pixmap(self, pixmap, max_width, max_height):
        """Масштабирует pixmap для режима докладчика - вписывает в окно с сохранением пропорций"""
        original_size = pixmap.size()
        original_width = original_size.width()
        original_height = original_size.height()
        
        # Вычисляем коэффициенты масштабирования
        width_ratio = max_width / original_width
        height_ratio = max_height / original_height
        
        # Используем меньший коэффициент, чтобы изображение полностью вписалось
        scale_factor = min(width_ratio, height_ratio)
        
        # Вычисляем новые размеры
        new_width = int(original_width * scale_factor)
        new_height = int(original_height * scale_factor)
        
        # Масштабируем изображение
        scaled_pixmap = pixmap.scaled(
            new_width, 
            new_height, 
            Qt.KeepAspectRatio, 
            Qt.SmoothTransformation
        )
        
        return scaled_pixmap
    
    def load_page(self, page_num):
        """Загружает и отображает страницу"""
        if 0 <= page_num < self.total_pages:
            self.current_page = page_num
            
            try:
                # Загружаем страницу с высоким разрешением
                page = self.doc.load_page(page_num)
                pix = page.get_pixmap(matrix=fitz.Matrix(3, 3))  # Увеличиваем разрешение для лучшего качества
                
                # Конвертируем в QPixmap
                img_data = pix.tobytes("ppm")
                qimage = QImage()
                qimage.loadFromData(img_data, "PPM")
                original_pixmap = QPixmap.fromImage(qimage)
                
                # Сохраняем ссылку на оригинальное изображение
                self.photo = original_pixmap
                
                # Получаем текущие размеры областей отображения
                main_label_size = self.pdf_label.size()
                
                # Масштабируем для основного окна (оставляем небольшие отступы)
                main_max_width = main_label_size.width() - 20
                main_max_height = main_label_size.height() - 20
                main_scaled_pixmap = self.get_scaled_pixmap(original_pixmap, main_max_width, main_max_height)
                
                # Обновляем основное окно
                self.pdf_label.setPixmap(main_scaled_pixmap)
                
                # Обновляем окно докладчика если оно открыто
                if self.presenter_window and self.presenter_window.isVisible():
                    presenter_label_size = self.presenter_label.size()
                    
                    # Для режима докладчика масштабируем с учетом всего доступного пространства
                    presenter_max_width = presenter_label_size.width() - 10
                    presenter_max_height = presenter_label_size.height() - 10
                    presenter_scaled_pixmap = self.get_presenter_scaled_pixmap(
                        original_pixmap, 
                        presenter_max_width, 
                        presenter_max_height
                    )
                    
                    self.presenter_label.setPixmap(presenter_scaled_pixmap)
                
                # Обновляем информацию о странице
                self.update_page_info()
                self.update_presenter_page_info()
                
                # Обновляем миниатюры
                self.thumbnail_widget.set_current_page(page_num)
                
            except Exception as e:
                print(f"Ошибка загрузки страницы {page_num}: {e}")
                traceback.print_exc()
    
    def resizeEvent(self, event):
        """Обработчик изменения размера главного окна - перерисовываем изображение"""
        super().resizeEvent(event)
        # При изменении размера окна перезагружаем текущую страницу с новым масштабированием
        if hasattr(self, 'current_page'):
            self.load_page(self.current_page)
    
    def showEvent(self, event):
        """Обработчик показа окна - перерисовываем изображение после открытия файла"""
        super().showEvent(event)
        # После открытия файла и показа окна перерисовываем изображение
        if hasattr(self, 'current_page'):
            QApplication.processEvents()  # Даем окну полностью отобразиться
            self.load_page(self.current_page)
    
    def update_page_info(self):
        """Обновляет информацию о текущей странице"""
        self.page_info.setText(f"Стр. {self.current_page + 1} из {self.total_pages}")
    
    def update_presenter_page_info(self):
        """Обновляет информацию о странице в окне докладчика"""
        # В режиме докладчика информация о странице не отображается
        pass
    
    def previous_page(self):
        """Переход к предыдущей странице"""
        if self.current_page > 0:
            self.load_page(self.current_page - 1)
    
    def next_page(self):
        """Переход к следующей странице"""
        if self.current_page < self.total_pages - 1:
            self.load_page(self.current_page + 1)
    
    def on_thumbnail_click(self, page_num):
        """Обработчик клика по миниатюре"""
        self.load_page(page_num)
    
    def toggle_presenter_mode(self):
        """Включает/выключает режим докладчика"""
        if self.presenter_window.isVisible():
            self.presenter_window.hide()
            self.presenter_btn.setText("📺 Режим докладчика")
        else:
            self.presenter_window.show()

            self.presenter_btn.setText("❌ Скрыть режим докладчика")
            # Синхронизируем отображение
            self.load_page(self.current_page)
            # Перемещаем окно докладчика на второй монитор если есть
            screens = QApplication.screens()
            if len(screens) > 1:
                # Второй монитор обычно screen[1]
                screen_geometry = screens[1].geometry()
                self.presenter_window.move(screen_geometry.x(), screen_geometry.y())
                # Убираем рамку и делаем полноэкранный вид
                self.presenter_window.setWindowFlags(Qt.FramelessWindowHint)
                # Полноэкранный режим
                self.presenter_window.showMaximized()
    
    def closeEvent(self, event):
        """Обработчик закрытия окна"""
        if self.presenter_window:
            self.presenter_window.close()
        self.doc.close()
        event.accept()

def main():
    # Если файл не передан как аргумент, открываем диалоговое окно выбора файла
    if len(sys.argv) != 2:
        try:
            # Создаем приложение для диалога
            app = QApplication(sys.argv)
            
            file_path, _ = QFileDialog.getOpenFileName(
                None, 
                "Выберите PDF файл", 
                "", 
                "PDF Files (*.pdf);;All Files (*)"
            )
            
            if not file_path:
                print("Файл не выбран.")
                return
                
        except Exception as e:
            print(f"Ошибка при выборе файла: {e}")
            input("Нажмите Enter для выхода...")
            return
    else:
        # Если файл передан как аргумент
        file_path = sys.argv[1]
    
    # Проверяем существование файла
    if not os.path.exists(file_path):
        print(f"Файл {file_path} не найден!")
        input("Нажмите Enter для выхода...")
        return
    
    try:
        # Если приложение еще не создано (при выборе через диалог), создаем его
        if not QApplication.instance():
            app = QApplication(sys.argv)
        else:
            app = QApplication.instance()
        
        # Устанавливаем стиль приложения
        app.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QPushButton {
                padding: 8px 16px;
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
            QLabel {
                font-size: 14px;
                padding: 5px;
            }
            QScrollArea {
                border: 1px solid #cccccc;
                background-color: white;
            }
        """)
        
        viewer = PDFViewer(file_path)
        viewer.show()
        
        sys.exit(app.exec_())
        
    except Exception as e:
        print(f"Произошла ошибка: {e}")
        traceback.print_exc()
        input("Нажмите Enter для выхода...")

if __name__ == "__main__":
    main()
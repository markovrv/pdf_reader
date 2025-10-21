@echo off
cd /d "%~dp0"

echo Running PDF Reader...
echo.

:: Проверяем, установлен ли Python в виртуальном окружении
if not exist "venv\Scripts\python.exe" (
    echo Ошибка: Виртуальное окружение не найдено!
    echo Убедитесь, что папка venv существует и зависимости установлены.
    pause
    exit /b 1
)

:: Активируем виртуальное окружение
call venv\Scripts\activate

:: Запускаем Python скрипт с выбранным файлом
python pdf_reader.py

:: Пауза чтобы увидеть результат
pause
@echo off
cd /d "%~dp0"

echo Running PDF Reader...
echo.

:: ���������, ���������� �� Python � ����������� ���������
if not exist "venv\Scripts\python.exe" (
    echo ������: ����������� ��������� �� �������!
    echo ���������, ��� ����� venv ���������� � ����������� �����������.
    pause
    exit /b 1
)

:: ���������� ����������� ���������
call venv\Scripts\activate

:: ��������� Python ������ � ��������� ������
python pdf_reader.py

:: ����� ����� ������� ���������
pause
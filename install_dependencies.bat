@echo off
echo ========================================
echo CAI DAT DEPENDENCIES - HE THONG BAI XE
echo ========================================
echo.

echo [1/3] Kiem tra Python...
python --version
if errorlevel 1 (
    echo ERROR: Python chua duoc cai dat!
    echo Vui long cai dat Python tu: https://www.python.org/downloads/
    pause
    exit /b 1
)
echo OK - Python da cai dat
echo.

echo [2/3] Nang cap pip...
python -m pip install --upgrade pip
echo.

echo [3/3] Cai dat cac package...
pip install flask==3.1.3
pip install flask-mail==0.10.0
pip install pdfkit==1.0.0
pip install pyodbc==5.3.0
pip install openpyxl==3.1.5
pip install stripe==15.0.1
pip install requests==2.33.1
pip install "qrcode[pil]==8.2"
pip install Pillow==12.2.0
pip install opencv-python==4.13.0.90
pip install pytesseract==0.3.13
pip install ultralytics==8.4.33
pip install python-dotenv==1.2.2

echo.
echo ========================================
echo HOAN THANH CAI DAT!
echo ========================================
echo.
echo Ban co the chay app bang lenh:
echo python app.py
echo.
pause

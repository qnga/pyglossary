rmdir /q /s build dist

pyinstaller --onefile --noconfirm pyglossary.spec

REM pyinstaller --onefile --noconfirm --windowed --noupx pyglossary.pyw
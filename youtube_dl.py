import sys
import os
from datetime import datetime

# 명령줄 인수가 있으면 사용하고, 없으면 사용자에게 물어봄
if len(sys.argv) > 1:
    url = sys.argv[1]
else:
    url = input("다운로드할 유튜브 URL을 입력하세요: ")

# 다운로드 폴더 생성
download_folder = os.path.expanduser("~/Downloads/유튜브다운로드")
os.makedirs(download_folder, exist_ok=True)

print(f"다운로드를 시작합니다: {url}")
print(f"저장 위치: {download_folder}")

# yt-dlp 명령 생성 및 실행
command = f'yt-dlp -f "best" -o "{download_folder}/%(title)s.%(ext)s" "{url}"'
print("실행 명령어:", command)
os.system(command)

print("\n다운로드가 완료되었습니다.")
print(f"파일은 {download_folder} 폴더에 있습니다.")
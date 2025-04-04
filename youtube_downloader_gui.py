import tkinter as tk
from tkinter import filedialog, StringVar
from pytube import YouTube

def browse_directory():
    # 폴더 선택 대화상자 열기
    directory = filedialog.askdirectory()
    if directory:
        path_var.set(directory)

def download_video():
    # 사용자 입력 가져오기
    url = url_var.get()
    output_path = path_var.get()
    
    # URL 유효성 검사
    if not url:
        status_var.set("URL을 입력하세요.")
        return
    
    try:
        # YouTube 객체 생성
        yt = YouTube(url)
        status_var.set(f"'{yt.title}' 다운로드 중...")
        window.update()
        
        # 최고 해상도 스트림 선택 및 다운로드
        yd = yt.streams.get_highest_resolution()
        yd.download(output_path)
        
        status_var.set("다운로드 완료!")
    except Exception as e:
        status_var.set(f"오류 발생: {str(e)}")

# GUI 윈도우 생성
window = tk.Tk()
window.title("유튜브 다운로더")
window.geometry("500x200")

# 변수 설정
url_var = StringVar()
path_var = StringVar()
status_var = StringVar()
path_var.set(".")  # 현재 디렉토리를 기본값으로 설정

# URL 입력 필드
tk.Label(window, text="유튜브 URL:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
tk.Entry(window, textvariable=url_var, width=50).grid(row=0, column=1, padx=5, pady=5)

# 저장 경로 선택
tk.Label(window, text="저장 경로:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
tk.Entry(window, textvariable=path_var, width=40).grid(row=1, column=1, padx=5, pady=5)
tk.Button(window, text="찾아보기", command=browse_directory).grid(row=1, column=2, padx=5, pady=5)

# 다운로드 버튼
tk.Button(window, text="다운로드", command=download_video, width=20).grid(row=2, column=1, padx=5, pady=10)

# 상태 표시
tk.Label(window, textvariable=status_var).grid(row=3, column=1, padx=5, pady=5)

# GUI 실행
window.mainloop()
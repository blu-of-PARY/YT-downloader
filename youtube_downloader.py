from pytube import YouTube # type: ignore

def download_video(url, output_path='.'):
    try:
        # YouTube 객체 생성
        yt = YouTube(url)
        
        # 비디오 정보 출력
        print(f"제목: {yt.title}")
        print(f"길이: {yt.length} 초")
        print(f"조회수: {yt.views}")
        
        # 최고 해상도 스트림 선택
        yd = yt.streams.get_highest_resolution()
        
        # 다운로드 시작
        print("다운로드 중...")
        yd.download(output_path)
        print("다운로드 완료!")
        
    except Exception as e:
        print(f"오류 발생: {str(e)}")

if __name__ == "__main__":
    video_url = input("다운로드할 유튜브 URL을 입력하세요: ")
    download_video(video_url)
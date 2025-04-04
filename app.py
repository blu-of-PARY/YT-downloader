from flask import Flask, render_template, request, send_file, send_from_directory
import yt_dlp
import os
import uuid
import threading

app = Flask(__name__)
DOWNLOAD_FOLDER = os.path.expanduser("~/Downloads/유튜브다운로드")
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

download_status = {}

# 서비스 워커 제공
@app.route('/static/js/service-worker.js')
def service_worker():
    return send_from_directory(os.path.join(app.root_path, 'static', 'js'),
                               'service-worker.js',
                               mimetype='application/javascript')

# 매니페스트 제공
@app.route('/static/manifest.json')
def manifest():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                              'manifest.json',
                              mimetype='application/json')

# 아이콘 제공
@app.route('/static/images/icons/<icon_name>')
def icons(icon_name):
    return send_from_directory(os.path.join(app.root_path, 'static', 'images', 'icons'),
                              icon_name)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        url = request.form.get('url')
        if url:
            # 다운로드 처리 코드...
            return render_template('index.html', message="다운로드 완료!")
        else:
            return render_template('index.html', message="URL을 입력하세요.")
    return render_template('index.html')

@app.route('/formats/<path:url>')
def get_formats(url):
    try:
        if '://' not in url:
            url = 'https://' + url

        ydl_opts = {
            'no_color': True,
            'quiet': True,
            'no_warnings': True,
            'youtube_include_dash_manifest': True
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # 비디오+오디오 결합 스트림 필터링
            video_formats = []
            for f in info.get('formats', []):
                if f.get('vcodec', 'none') != 'none' and f.get('acodec', 'none') != 'none':
                    format_info = {
                        'format_id': f.get('format_id'),
                        'ext': f.get('ext'),
                        'resolution': f.get('resolution', 'unknown'),
                        'format_note': f.get('format_note', ''),
                        'filesize': f.get('filesize', 0)
                    }
                    
                    if format_info['filesize']:
                        format_info['filesize_mb'] = round(format_info['filesize'] / (1024 * 1024), 2)
                        format_info['display'] = f"{format_info['resolution']} ({format_info['ext']}) - {format_info['filesize_mb']} MB"
                    else:
                        format_info['display'] = f"{format_info['resolution']} ({format_info['ext']})"
                    
                    video_formats.append(format_info)

            # 고화질 비디오 스트림 찾기
            video_only_formats = []
            available_heights = set()  # 사용 가능한 해상도 높이를 저장
            
            for f in info.get('formats', []):
                # 비디오 코덱이 있고, 오디오 코덱이 없는 스트림 찾기
                if (f.get('vcodec', 'none') != 'none' and 
                    f.get('acodec', 'none') == 'none' and 
                    f.get('height') is not None):
                    available_heights.add(f.get('height'))
                    
                    # 스트림 정보 저장 (720p 이상만)
                    if f.get('height', 0) >= 720:
                        format_info = {
                            'format_id': f"{f.get('format_id')}+bestaudio",
                            'ext': 'mp4',
                            'resolution': f"{f.get('height')}p", 
                            'height': f.get('height', 0),
                            'filesize': f.get('filesize', 0)
                        }
                        
                        # 파일 크기 표시
                        if format_info['filesize']:
                            format_info['filesize_mb'] = round(format_info['filesize'] / (1024 * 1024), 2)
                            format_info['display'] = f"{format_info['resolution']} (고화질) - {format_info['filesize_mb']} MB"
                        else:
                            format_info['display'] = f"{format_info['resolution']} (고화질)"
                        
                        video_only_formats.append(format_info)
            
            # 해상도 기준으로 정렬
            video_only_formats = sorted(video_only_formats, 
                                        key=lambda x: x.get('height', 0), 
                                        reverse=True)
            
            # 중복 해상도 제거 (각 해상도당 가장 좋은 품질만 유지)
            unique_formats = {}
            for fmt in video_only_formats:
                height = fmt['height']
                if height not in unique_formats:
                    unique_formats[height] = fmt
            
            high_quality_formats = list(unique_formats.values())
            
            # 오디오만 있는 옵션 추가
            audio_formats = []
            for f in info.get('formats', []):
                if f.get('vcodec', 'none') == 'none' and f.get('acodec', 'none') != 'none':
                    format_info = {
                        'format_id': f.get('format_id'),
                        'ext': f.get('ext'),
                        'format_note': f.get('format_note', '오디오만'),
                        'filesize': f.get('filesize', 0)
                    }
                    
                    if format_info['filesize']:
                        format_info['filesize_mb'] = round(format_info['filesize'] / (1024 * 1024), 2)
                        format_info['display'] = f"오디오만 ({format_info['ext']}) - {format_info['filesize_mb']} MB"
                    else:
                        format_info['display'] = f"오디오만 ({format_info['ext']})"
                    
                    audio_formats.append(format_info)
            
            # 가장 좋은 품질 옵션 추가
            best_format = {
                'format_id': 'best',
                'display': '최상의 품질 (자동)'
            }
            
            # 오디오만 옵션 추가
            audio_only = {
                'format_id': 'bestaudio',
                'display': '최상의 오디오만 (MP3)'
            }
            
            # 모든 옵션을 하나의 리스트로 합치기
            formats = [best_format] + high_quality_formats + video_formats + [audio_only] + audio_formats
            
            return {
                'title': info.get('title', ''),
                'thumbnail': info.get('thumbnail', ''),
                'duration': info.get('duration', 0),
                'formats': formats
            }
    
    except Exception as e:
        print(f"오류 발생: {str(e)}")
        return {'error': str(e)}, 500

@app.route('/download', methods=['POST'])
def download():
    url = request.form['url']
    format_id = request.form.get('format_id', 'best')  # 기본값은 최상의 품질
    
    if not url:
        return "URL을 입력해주세요", 400
    
    download_id = str(uuid.uuid4())
    download_status[download_id] = {
        'status': '다운로드 준비 중...',
        'progress': 0,
        'filename': None
    }
    
    # 백그라운드로 다운로드 실행
    thread = threading.Thread(target=download_video, args=(url, download_id, format_id))
    thread.daemon = True
    thread.start()
    
    return {'download_id': download_id}

def download_video(url, download_id, format_id='best'):
    try:
        # 저장 경로 확인
        os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)
        
        # 기본 출력 경로 설정 (실제 파일명은 나중에 결정)
        temp_filename = f"{download_id}.%(ext)s"
        output_template = os.path.join(DOWNLOAD_FOLDER, temp_filename)
        
        def progress_hook(d):
            if d['status'] == 'downloading':
                # ANSI 색상 코드 제거
                percent_str = d.get('_percent_str', '0%')
                # 색상 코드 및 기타 문자 제거
                clean_percent = ''.join(c for c in percent_str if c.isdigit() or c == '.')
                try:
                    # 숫자만 추출하여 변환
                    percent = float(clean_percent) if clean_percent else 0
                    download_status[download_id]['progress'] = percent
                    download_status[download_id]['status'] = f'다운로드 중... {percent:.1f}%'
                except ValueError:
                    download_status[download_id]['progress'] = 0
                    download_status[download_id]['status'] = '다운로드 중...'
            elif d['status'] == 'finished':
                download_status[download_id]['status'] = '변환 중...'
                # 여기서 실제 파일 경로 저장
                if 'filename' in d:
                    download_status[download_id]['filepath'] = d['filename']
        
        # 오디오만 다운로드 설정
        if format_id == 'bestaudio':
            ydl_opts = {
                'format': format_id,
                'outtmpl': output_template,
                'progress_hooks': [progress_hook],
                'no_color': True,
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }]
            }
        # 고화질 비디오+오디오 결합 설정
        elif '+' in format_id:
            ydl_opts = {
                'format': format_id,
                'outtmpl': output_template,
                'progress_hooks': [progress_hook],
                'no_color': True,
                # FFmpeg 관련 설정 추가
                'merge_output_format': 'mp4'
            }
        # 일반 다운로드 설정
        else:
            ydl_opts = {
                'format': format_id,
                'outtmpl': output_template,
                'progress_hooks': [progress_hook],
                'no_color': True,
            }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get('title', '다운로드된 미디어')
            download_status[download_id]['filename'] = title
            
            # 파일 경로가 아직 설정되지 않았다면
            if 'filepath' not in download_status[download_id]:
                # 확장자 결정
                ext = 'mp3' if format_id == 'bestaudio' else 'mp4'
                filepath = os.path.join(DOWNLOAD_FOLDER, f"{download_id}.{ext}")
                download_status[download_id]['filepath'] = filepath
            
            # 파일이 실제로 존재하는지 확인
            if os.path.exists(download_status[download_id]['filepath']):
                download_status[download_id]['status'] = '완료'
            else:
                # 다운로드는 성공했지만 파일이 없는 경우 (파일명이 다르게 저장됐을 수 있음)
                # 폴더에서 download_id로 시작하는 파일 찾기
                for filename in os.listdir(DOWNLOAD_FOLDER):
                    if filename.startswith(download_id):
                        filepath = os.path.join(DOWNLOAD_FOLDER, filename)
                        download_status[download_id]['filepath'] = filepath
                        download_status[download_id]['status'] = '완료'
                        break
                else:
                    download_status[download_id]['status'] = '오류: 다운로드된 파일을 찾을 수 없습니다'
            
    except Exception as e:
        download_status[download_id]['status'] = f'오류: {str(e)}'
        print(f"다운로드 오류: {str(e)}")

@app.route('/status/<download_id>')
def status(download_id):
    if download_id in download_status:
        return download_status[download_id]
    return {'status': '존재하지 않는 다운로드입니다.'}, 404

@app.route('/get_file/<download_id>')
def get_file(download_id):
    if download_id in download_status and download_status[download_id]['status'] == '완료':
        filepath = download_status[download_id]['filepath']
        
        # 파일이 실제로 존재하는지 다시 확인
        if not os.path.exists(filepath):
            return "파일을 찾을 수 없습니다: " + filepath, 404
        
        filename = download_status[download_id]['filename']
        ext = os.path.splitext(filepath)[1]  # 확장자 가져오기
        
        return send_file(
            filepath,
            as_attachment=True,
            download_name=f"{filename}{ext}"
        )
    return "파일을 찾을 수 없습니다.", 404

# 자막 정보 가져오기 함수 추가
@app.route('/subtitles/<path:url>')
def get_subtitles(url):
    try:
        # URL 형식 검사 및 수정
        if '://' not in url:
            url = 'https://' + url
        
        ydl_opts = {
            'no_color': True,
            'quiet': True,
            'no_warnings': True,
            'skip_download': True,  # 비디오 다운로드 건너뛰기
            'writesubtitles': True,  # 자막 정보 가져오기
            'listsubtitles': True,   # 자막 목록 출력
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # 자막 정보 추출
            subtitles = {}
            if 'subtitles' in info:
                for lang, sub_info in info['subtitles'].items():
                    formats = []
                    for fmt in sub_info:
                        formats.append({
                            'ext': fmt.get('ext', ''),
                            'format_id': lang + '-' + fmt.get('ext', '')
                        })
                    
                    if formats:
                        # 언어 이름 가져오기 (ex: 'en' -> 'English')
                        lang_name = get_language_name(lang)
                        subtitles[lang] = {
                            'name': lang_name,
                            'formats': formats,
                            'code': lang
                        }
            
            # 자동 생성 자막 정보 추가
            if 'automatic_captions' in info:
                for lang, sub_info in info['automatic_captions'].items():
                    formats = []
                    for fmt in sub_info:
                        formats.append({
                            'ext': fmt.get('ext', ''),
                            'format_id': lang + '-auto-' + fmt.get('ext', '')
                        })
                    
                    if formats:
                        lang_name = get_language_name(lang) + ' (자동 생성)'
                        subtitles[lang + '-auto'] = {
                            'name': lang_name,
                            'formats': formats,
                            'code': lang,
                            'auto': True
                        }
            
            return {
                'title': info.get('title', ''),
                'subtitles': subtitles
            }
    
    except Exception as e:
        print(f"자막 정보 가져오기 오류: {str(e)}")
        return {'error': str(e)}, 500

# 언어 코드를 이름으로 변환하는 함수
def get_language_name(lang_code):
    language_map = {
        'ko': '한국어', 'en': '영어', 'ja': '일본어', 'zh': '중국어',
        'es': '스페인어', 'fr': '프랑스어', 'de': '독일어', 'ru': '러시아어',
        'it': '이탈리아어', 'pt': '포르투갈어', 'ar': '아랍어', 'hi': '힌디어',
        'th': '태국어', 'vi': '베트남어'
    }
    return language_map.get(lang_code, lang_code)

# 자막 다운로드 함수 추가
@app.route('/download_subtitle', methods=['POST'])
def download_subtitle():
    url = request.form['url']
    format_id = request.form.get('format_id', '')  # 언어-확장자 형식
    
    if not url or not format_id:
        return "URL과 자막 형식을 입력해주세요", 400
    
    download_id = str(uuid.uuid4())
    download_status[download_id] = {
        'status': '자막 다운로드 준비 중...',
        'progress': 0,
        'filename': None
    }
    
    # 백그라운드로 다운로드 실행
    thread = threading.Thread(target=download_subtitle_file, args=(url, download_id, format_id))
    thread.daemon = True
    thread.start()
    
    return {'download_id': download_id}

def download_subtitle_file(url, download_id, format_id):
    try:
        # 형식 ID 파싱
        lang, ext = format_id.rsplit('-', 1)
        is_auto = False
        
        if '-auto-' in format_id:
            lang = lang.replace('-auto', '')
            is_auto = True
        
        # 저장 경로 확인
        os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)
        
        # 기본 출력 경로 설정
        output_template = os.path.join(DOWNLOAD_FOLDER, f"{download_id}.%(ext)s")
        
        ydl_opts = {
            'skip_download': True,  # 비디오는 다운로드하지 않음
            'outtmpl': output_template,
            'no_color': True,
        }
        
        # 자동 생성 자막 또는 일반 자막 설정
        if is_auto:
            ydl_opts['writeautomaticsub'] = True
            ydl_opts['subtitleslangs'] = [lang]
        else:
            ydl_opts['writesubtitles'] = True
            ydl_opts['subtitleslangs'] = [lang]
        
        # 자막 형식 설정
        ydl_opts['subtitlesformat'] = ext
        
        download_status[download_id]['status'] = '자막 다운로드 중...'
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get('title', '자막 파일')
            download_status[download_id]['filename'] = f"{title}.{ext}"
            
            # 파일 검색
            for filename in os.listdir(DOWNLOAD_FOLDER):
                if filename.startswith(download_id) or filename.endswith(f".{lang}.{ext}"):
                    filepath = os.path.join(DOWNLOAD_FOLDER, filename)
                    download_status[download_id]['filepath'] = filepath
                    download_status[download_id]['status'] = '완료'
                    break
            else:
                download_status[download_id]['status'] = '오류: 자막 파일을 찾을 수 없습니다'
            
    except Exception as e:
        download_status[download_id]['status'] = f'오류: {str(e)}'
        print(f"자막 다운로드 오류: {str(e)}")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5050, debug=True)

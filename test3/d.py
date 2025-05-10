import speech_recognition as sr
import datetime
import os
import time
import threading
import keyboard
import json
from pydub import AudioSegment
from pydub.silence import split_on_silence

class LectureRecorder:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.mic = sr.Microphone()
        self.running = False
        self.pause = False
        self.current_subject = "기본 강의"
        self.today = datetime.datetime.now().strftime("%Y-%m-%d")
        self.notes_folder = "lecture_notes"
        self.audio_folder = "lecture_audio"
        self.config_file = "recorder_config.json"
        self.subjects = ["기본 강의", "수학", "물리학", "프로그래밍", "기타"]
        self.config = self.load_config()
        
        # 폴더 생성
        for folder in [self.notes_folder, self.audio_folder]:
            if not os.path.exists(folder):
                os.makedirs(folder)
        
        # 음성 인식 설정
        self.recognizer.energy_threshold = self.config.get("energy_threshold", 4000)
        self.recognizer.dynamic_energy_threshold = self.config.get("dynamic_energy_threshold", True)
        self.recognizer.pause_threshold = self.config.get("pause_threshold", 0.8)
        
    def load_config(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                pass
        return {
            "energy_threshold": 4000,
            "dynamic_energy_threshold": True,
            "pause_threshold": 0.8,
            "language": "ko-KR",
            "timeout": 60,
            "last_subject": "기본 강의"
        }
    
    def save_config(self):
        self.config["last_subject"] = self.current_subject
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=4)
    
    def select_subject(self):
        print("\n강의 과목 선택:")
        for idx, subject in enumerate(self.subjects, 1):
            print(f"{idx}. {subject}")
        print(f"{len(self.subjects) + 1}. 새 강의 추가")
        
        while True:
            try:
                choice = int(input("번호 선택: "))
                if 1 <= choice <= len(self.subjects):
                    self.current_subject = self.subjects[choice-1]
                    break
                elif choice == len(self.subjects) + 1:
                    new_subject = input("새 강의명 입력: ")
                    if new_subject.strip():
                        self.subjects.append(new_subject)
                        self.current_subject = new_subject
                        break
            except ValueError:
                pass
            print("유효한 번호를 입력해주세요.")
    
    def get_filename(self, file_type):
        timestamp = datetime.datetime.now().strftime("%H-%M-%S")
        subject_safe = self.current_subject.replace(" ", "_")
        
        if file_type == "text":
            folder = self.notes_folder
            ext = "txt"
        else:  # audio
            folder = self.audio_folder
            ext = "wav"
            
        return os.path.join(folder, f"{self.today}_{subject_safe}_{timestamp}.{ext}")
    
    def process_audio_to_text(self, audio_data):
        try:
            text = self.recognizer.recognize_google(audio_data, language=self.config.get("language", "ko-KR"))
            return text
        except sr.UnknownValueError:
            return "[음성 인식 실패]"
        except sr.RequestError:
            return "[음성 인식 서비스 오류]"
    
    def save_text(self, text):
        notes_file = self.get_filename("text")
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        
        with open(notes_file, "a", encoding="utf-8") as file:
            file.write(f"[{timestamp}] {text}\n\n")
        
        return notes_file
    
    def save_audio(self, audio_data):
        try:
            audio_file = self.get_filename("audio")
            with open(audio_file, "wb") as f:
                f.write(audio_data.get_wav_data())
            return audio_file
        except Exception as e:
            print(f"오디오 저장 오류: {e}")
            return None
    
    def status_display(self):
        while self.running:
            if self.pause:
                status = "일시정지"
            else:
                status = "녹음 중"
                
            print(f"\r현재 상태: {status} | 과목: {self.current_subject} | 날짜: {self.today} | 'p': 일시정지/재개 | 'q': 종료", end="")
            time.sleep(0.5)
    
    def hotkey_handler(self):
        while self.running:
            if keyboard.is_pressed('p'):
                self.pause = not self.pause
                time.sleep(0.3)  # 키 입력 중복 방지
            elif keyboard.is_pressed('q'):
                self.running = False
                time.sleep(0.3)
    
    def start(self):
        self.select_subject()
        self.running = True
        self.pause = False
        
        # 상태 표시 스레드 시작
        status_thread = threading.Thread(target=self.status_display)
        status_thread.daemon = True
        status_thread.start()
        
        # 핫키 처리 스레드 시작
        hotkey_thread = threading.Thread(target=self.hotkey_handler)
        hotkey_thread.daemon = True
        hotkey_thread.start()
        
        # 시작 정보 기록
        print("\n" + "="*50)
        print(f"강의 녹음 시작: {self.current_subject}")
        print("="*50)
        
        notes_file = self.get_filename("text")
        with open(notes_file, "w", encoding="utf-8") as file:
            file.write(f"강의: {self.current_subject}\n")
            file.write(f"날짜: {self.today}\n")
            file.write("="*50 + "\n\n")
        
        # 메인 녹음 루프
        try:
            while self.running:
                if not self.pause:
                    with self.mic as source:
                        print("\n주변 소음 조정 중...")
                        self.recognizer.adjust_for_ambient_noise(source)
                        print("듣는 중...")
                        
                        try:
                            audio = self.recognizer.listen(source, timeout=self.config.get("timeout", 60))
                            
                            # 텍스트 변환 및 저장
                            text = self.process_audio_to_text(audio)
                            if text:
                                print(f"\n인식된 텍스트: {text}")
                                self.save_text(text)
                                
                                # 선택적으로 오디오 저장
                                if self.config.get("save_audio", False):
                                    self.save_audio(audio)
                        
                        except sr.WaitTimeoutError:
                            print("\n일정 시간 동안 말소리가 감지되지 않았습니다.")
                else:
                    time.sleep(1)  # 일시정지 상태에서 CPU 사용량 줄이기
                    
        except KeyboardInterrupt:
            pass
        finally:
            print("\n" + "="*50)
            print("강의 녹음 종료")
            print("="*50)
            self.save_config()
    
    def settings(self):
        print("\n=== 설정 메뉴 ===")
        print("1. 언어 설정")
        print("2. 음성 감지 민감도 설정")
        print("3. 오디오 저장 여부")
        print("4. 변환 시간 간격 설정")
        print("5. 뒤로 가기")
        
        choice = input("선택: ")
        
        if choice == "1":
            print("\n언어 코드 예시:")
            print("한국어: ko-KR")
            print("영어(미국): en-US")
            print("영어(영국): en-GB")
            print("일본어: ja-JP")
            print("중국어(간체): zh-CN")
            lang = input(f"언어 코드 입력 (현재: {self.config.get('language', 'ko-KR')}): ")
            if lang.strip():
                self.config["language"] = lang
                
        elif choice == "2":
            try:
                value = int(input(f"민감도 설정 (현재: {self.config.get('energy_threshold', 4000)}, 낮을수록 민감): "))
                self.config["energy_threshold"] = value
                self.recognizer.energy_threshold = value
            except ValueError:
                print("유효한 숫자를 입력해주세요.")
                
        elif choice == "3":
            save = input(f"오디오 저장 (현재: {'예' if self.config.get('save_audio', False) else '아니오'}) [y/n]: ").lower()
            self.config["save_audio"] = save == 'y'
            
        elif choice == "4":
            try:
                timeout = int(input(f"변환 간격(초) (현재: {self.config.get('timeout', 60)}): "))
                self.config["timeout"] = timeout
            except ValueError:
                print("유효한 숫자를 입력해주세요.")
        
        self.save_config()

def main():
    recorder = LectureRecorder()
    
    while True:
        print("\n=== 강의 녹음 시스템 ===")
        print("1. 녹음 시작")
        print("2. 설정")
        print("3. 종료")
        
        choice = input("선택: ")
        
        if choice == "1":
            recorder.start()
        elif choice == "2":
            recorder.settings()
        elif choice == "3":
            print("프로그램을 종료합니다.")
            break
        else:
            print("유효한 옵션을 선택해주세요.")

if __name__ == "__main__":
    main()
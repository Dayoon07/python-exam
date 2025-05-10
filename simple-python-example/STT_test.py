import speech_recognition as sr

recognizer = sr.Recognizer()
mic = sr.Microphone()

print("강의 녹음을 시작합니다. (Ctrl + C로 종료)")

# 텍스트 파일 초기화 (덮어쓰기 방지)
with open("lecture_notes.txt", "w", encoding="utf-8") as file:
    file.write("강의 녹음 시작\n")

while True:
    try:
        with mic as source:
            recognizer.adjust_for_ambient_noise(source)
            print("듣는 중...")
            audio = recognizer.listen(source, timeout=60)  # 60초마다 녹음 후 변환

        text = recognizer.recognize_google(audio, language="ko-KR")
        print("변환된 텍스트:", text)

        # 파일에 변환된 텍스트 저장
        with open("notes.txt", "a", encoding="utf-8") as file:
            file.write(text + "\n")

    except sr.UnknownValueError:
        print("음성을 인식할 수 없습니다.")
    except sr.RequestError:
        print("음성 인식 서비스 오류 발생")
    except KeyboardInterrupt:
        print("\n강의 녹음 종료")
        break

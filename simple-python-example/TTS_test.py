from gtts import gTTS
import playsound
import os

# 텍스트 정의
text = "안녕? 나는 text to speech가 잘 작동하는지 테스트하고 있어"

file = os.path.join(os.getcwd(), "text.mp3")  # 현재 폴더에 저장

# TTS 객체 생성
tts = gTTS(text=text, lang='ko')

# 음성 파일 저장
tts.save(file)

playsound.playsound(file)
print(playsound.playsound(text))


import cv2
import mediapipe as mp
import numpy as np
import pygame
import pygame.midi

# MediaPipe 손 감지 초기화
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
hands = mp_hands.Hands(
    max_num_hands=2,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.5
)

# PyGame 및 MIDI 초기화
pygame.init()
pygame.midi.init()

# 사용 가능한 MIDI 출력 장치 확인
output_id = pygame.midi.get_default_output_id()
if output_id == -1:
    print("MIDI 출력 장치가 없습니다. 소리가 재생되지 않을 수 있습니다.")
    output = None
else:
    output = pygame.midi.Output(output_id)
    # 그랜드 피아노 악기 설정 (프로그램 변경: 채널 0, 악기 0)
    output.set_instrument(0, channel=0)

# 피아노 건반 설정
class PianoKey:
    def __init__(self, x, width, height, note, is_white=True):
        self.x = x
        self.width = width
        self.height = height
        self.note = note  # MIDI 노트 번호
        self.is_white = is_white
        self.is_pressed = False
        # 흰 건반은 위에서부터, 검은 건반은 위에서 60% 위치에서 시작
        self.y = 0 if is_white else 0

    def contains_point(self, point_x, point_y):
        # 건반 영역 내에 있는지 확인
        if self.is_white:
            return (self.x <= point_x <= self.x + self.width and
                    self.y <= point_y <= self.y + self.height)
        else:
            return (self.x <= point_x <= self.x + self.width and
                    self.y <= point_y <= self.y + self.height)

    def draw(self, image):
        # 흰 건반 또는 검은 건반 색상 설정
        if self.is_white:
            color = (200, 200, 200) if not self.is_pressed else (150, 255, 150)
        else:
            color = (50, 50, 50) if not self.is_pressed else (100, 200, 100)
        
        # 현재 노트 표시
        font_scale = 0.4
        text_color = (0, 0, 0) if self.is_white else (255, 255, 255)
        
        x1, y1 = int(self.x), int(self.y)
        x2, y2 = int(self.x + self.width), int(self.y + self.height)
        
        cv2.rectangle(image, (x1, y1), (x2, y2), color, -1)
        cv2.rectangle(image, (x1, y1), (x2, y2), (0, 0, 0), 1)
        cv2.putText(image, f"{self.note}", 
                    (x1 + 5, y2 - 10), 
                    cv2.FONT_HERSHEY_SIMPLEX, font_scale, text_color, 1)

    def play(self):
        if output is not None and not self.is_pressed:
            output.note_on(self.note, velocity=127, channel=0)
            self.is_pressed = True

    def release(self):
        if output is not None and self.is_pressed:
            output.note_off(self.note, velocity=0, channel=0)
            self.is_pressed = False

# 피아노 건반 생성 함수
def create_piano_keys(start_x, white_key_width, black_key_width, white_key_height, black_key_height):
    keys = []
    
    # C4 (미디 노트 60)부터 시작하는 한 옥타브 건반 생성
    # 흰 건반: C, D, E, F, G, A, B
    # 검은 건반: C#, D#, F#, G#, A#
    
    white_notes = [60, 62, 64, 65, 67, 69, 71]  # C4, D4, E4, F4, G4, A4, B4
    black_notes = [61, 63, 66, 68, 70]  # C#4, D#4, F#4, G#4, A#4
    
    # 흰 건반 위치
    white_positions = [0, 1, 2, 3, 4, 5, 6]
    # 검은 건반 위치 (흰 건반 사이)
    black_positions = [0.6, 1.6, 3.6, 4.6, 5.6]
    
    # 흰 건반 생성
    for i, note in enumerate(white_notes):
        x = start_x + (white_key_width * white_positions[i])
        keys.append(PianoKey(x, white_key_width, white_key_height, note, True))
    
    # 검은 건반 생성
    for i, note in enumerate(black_notes):
        x = start_x + (white_key_width * black_positions[i]) - (black_key_width / 2)
        keys.append(PianoKey(x, black_key_width, black_key_height, note, False))
    
    return keys

# 손가락 끝점 감지 함수
def get_fingertips(hand_landmarks, image_width, image_height):
    # 손가락 끝 인덱스 (엄지, 검지, 중지, 약지, 소지)
    fingertip_ids = [4, 8, 12, 16, 20]
    fingertips = []
    
    for tip_id in fingertip_ids:
        x = int(hand_landmarks.landmark[tip_id].x * image_width)
        y = int(hand_landmarks.landmark[tip_id].y * image_height)
        fingertips.append((x, y))
    
    return fingertips

# 웹캠 설정
cap = cv2.VideoCapture(0)
cap_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
cap_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

# 피아노 설정
piano_width = cap_width
white_key_width = piano_width // 7  # 7개의 흰 건반
white_key_height = 150
black_key_width = white_key_width // 2
black_key_height = int(white_key_height * 0.6)  # 변경된 부분
start_x = 0

# 피아노 건반 생성
piano_keys = create_piano_keys(start_x, white_key_width, black_key_width, 
                               white_key_height, black_key_height)

# 거울 모드 설정
mirror_mode = True

try:
    while cap.isOpened():
        success, image = cap.read()
        if not success:
            print("카메라를 찾을 수 없습니다.")
            break
        
        # 거울 모드 (좌우 반전)
        if mirror_mode:
            image = cv2.flip(image, 1)
        
        # MediaPipe 처리를 위한 이미지 변환
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = hands.process(image_rgb)
        
        # 손이 감지되었는지 확인
        pressed_keys = set()  # 현재 프레임에서 눌린 키를 추적
        
        # 피아노 건반 그리기
        # 먼저 검은 건반을 그리기 위해 흰 건반과 검은 건반 분리
        white_keys = [key for key in piano_keys if key.is_white]
        black_keys = [key for key in piano_keys if not key.is_white]
        
        # 먼저 흰 건반 그리기
        for key in white_keys:
            key.draw(image)
        
        # 그 다음 검은 건반 그리기 (겹치도록)
        for key in black_keys:
            key.draw(image)
        
        # 손이 감지되면 처리
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                # 손 랜드마크 그리기
                mp_drawing.draw_landmarks(
                    image, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                
                # 손가락 끝점 가져오기
                fingertips = get_fingertips(hand_landmarks, cap_width, cap_height)
                
                # 손가락 끝에 원 표시
                for x, y in fingertips:
                    cv2.circle(image, (x, y), 8, (0, 255, 255), -1)
                    
                    # 각 건반을 확인하여 누름 여부 판단
                    for key in piano_keys:
                        if key.contains_point(x, y):
                            key.play()
                            pressed_keys.add(key)
        
        # 이전에 눌렸지만 현재 프레임에서 눌리지 않은 키 해제
        for key in piano_keys:
            if key not in pressed_keys and key.is_pressed:
                key.release()
        
        # 지시사항 표시
        cv2.putText(image, "손가락 끝으로 건반을 터치하세요", 
                    (10, cap_height - 20), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        
        # 화면에 표시
        cv2.imshow('Virtual Piano', image)
        
        # 'q' 키를 누르면 종료
        if cv2.waitKey(5) & 0xFF == ord('q'):
            break

finally:
    # 모든 건반 소리 정지
    if output is not None:
        for key in piano_keys:
            if key.is_pressed:
                key.release()
        output.close()
    
    pygame.midi.quit()
    pygame.quit()
    cap.release()
    cv2.destroyAllWindows()

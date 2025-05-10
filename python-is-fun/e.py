import cv2
import mediapipe as mp
import numpy as np
import math
import random

# MediaPipe 포즈 및 손 감지 모듈 초기화
mp_pose = mp.solutions.pose
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles

# 포즈 및 손 감지 설정
pose = mp_pose.Pose(
    static_image_mode=False,
    model_complexity=1,
    enable_segmentation=False,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=2,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

# 신경망 펄스 애니메이션 설정
class NeuralPulse:
    def __init__(self, start_idx, end_idx, speed=0.05):
        self.start_idx = start_idx
        self.end_idx = end_idx
        self.position = 0.0  # 0.0(시작점)에서 1.0(끝점)까지
        self.speed = speed
        self.active = True
        self.color = (random.randint(150, 255), random.randint(150, 255), 0)  # 노란색 계열 무작위 색상
    
    def update(self):
        self.position += self.speed
        if self.position > 1.0:
            self.position = 0.0
            # 액티브 상태 랜덤하게 토글(일부만 활성화되도록)
            self.active = random.random() > 0.3
            # 색상 업데이트
            self.color = (random.randint(150, 255), random.randint(150, 255), 0)

# 전신 신경망 연결 정의
def get_pose_connections():
    # 기본 MediaPipe POSE_CONNECTIONS에 추가적인 신경망 연결 추가
    connections = []
    
    # 기본 포즈 연결
    for connection in mp_pose.POSE_CONNECTIONS:
        connections.append(connection)
    
    # 추가 신경망 연결 (중앙 척추에서 팔다리로 연결되는 신경)
    central_connections = [
        # 척추에서 팔로 연결되는 신경
        (mp_pose.PoseLandmark.LEFT_SHOULDER, mp_pose.PoseLandmark.RIGHT_SHOULDER),
        (mp_pose.PoseLandmark.LEFT_SHOULDER, mp_pose.PoseLandmark.LEFT_HIP),
        (mp_pose.PoseLandmark.RIGHT_SHOULDER, mp_pose.PoseLandmark.RIGHT_HIP),
        
        # 추가 중앙 신경 연결
        (mp_pose.PoseLandmark.NOSE, mp_pose.PoseLandmark.LEFT_SHOULDER),
        (mp_pose.PoseLandmark.NOSE, mp_pose.PoseLandmark.RIGHT_SHOULDER),
    ]
    
    connections.extend(central_connections)
    return connections

# 신경망 시각화 함수
def draw_neural_network(image, landmarks, connections, pulses, mirror_mode=False):
    h, w, c = image.shape
    overlay = image.copy()
    
    # 관절 위치 추출
    points = []
    for landmark in landmarks:
        x = int(landmark.x * w)
        y = int(landmark.y * h)
        # 거울 모드는 이미지 자체에서 처리했으므로 여기서는 좌표 변환 불필요
        points.append((x, y))
    
    # 신경망 연결선 그리기
    for connection in connections:
        start_idx, end_idx = connection
        if start_idx < len(points) and end_idx < len(points):  # 인덱스 범위 확인
            cv2.line(overlay, points[start_idx], points[end_idx], 
                    (0, 255, 0), 2)
    
    # 신경 펄스 애니메이션 그리기
    for pulse in pulses:
        if pulse.active and pulse.start_idx < len(points) and pulse.end_idx < len(points):
            start_point = points[pulse.start_idx]
            end_point = points[pulse.end_idx]
            
            # 펄스 위치 계산
            pulse_x = int(start_point[0] + (end_point[0] - start_point[0]) * pulse.position)
            pulse_y = int(start_point[1] + (end_point[1] - start_point[1]) * pulse.position)
            
            # 펄스 그리기
            cv2.circle(overlay, (pulse_x, pulse_y), 4, pulse.color, -1)
            
            # 작은 글로우 효과
            cv2.circle(overlay, (pulse_x, pulse_y), 6, pulse.color, 1)
    
    # 신경 노드(관절) 그리기
    for point in points:
        cv2.circle(overlay, point, 5, (0, 0, 255), -1)
    
    # 오버레이 적용
    alpha = 0.7  # 투명도
    cv2.addWeighted(overlay, alpha, image, 1 - alpha, 0, image)
    return image

# 웹캠 설정
cap = cv2.VideoCapture(0)

# 거울 모드 설정 (기본값: 켜짐)
mirror_mode = True

# 펄스 애니메이션 초기화
pose_connections = get_pose_connections()
pulses = []

# 각 연결에 대한 펄스 생성
for connection in pose_connections:
    # 30% 확률로 시작 시 활성화
    active = random.random() > 0.7
    speed = random.uniform(0.01, 0.05)  # 다양한 속도로 움직이는 펄스
    pulses.append(NeuralPulse(connection[0], connection[1], speed))

while cap.isOpened():
    success, image = cap.read()
    if not success:
        print("카메라를 찾을 수 없습니다.")
        break

    # 거울 모드인 경우에만 이미지 좌우 반전
    if mirror_mode:
        image = cv2.flip(image, 1)
    
    # 이미지를 BGR에서 RGB로 변환
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    # MediaPipe로 포즈 감지
    pose_results = pose.process(image_rgb)
    
    # MediaPipe로 손 감지
    hands_results = hands.process(image_rgb)
    
    # 다시 BGR로 변환
    image = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR)
    
    # 신경망 시각화를 위한 이미지
    vis_image = image.copy()
    
    # 포즈가 감지되면 신경망 시각화
    if pose_results.pose_landmarks:
        # 기본 포즈 랜드마크 그리기
        mp_drawing.draw_landmarks(
            vis_image, 
            pose_results.pose_landmarks, 
            mp_pose.POSE_CONNECTIONS,
            landmark_drawing_spec=mp_drawing_styles.get_default_pose_landmarks_style())
        
        # 펄스 업데이트
        for pulse in pulses:
            pulse.update()
        
        # 신경망 시각화 오버레이
        vis_image = draw_neural_network(
            vis_image, 
            pose_results.pose_landmarks.landmark, 
            pose_connections, 
            pulses,
            mirror_mode
        )
    
    # 손이 감지되면 추가
    if hands_results.multi_hand_landmarks:
        for hand_landmarks in hands_results.multi_hand_landmarks:
            mp_drawing.draw_landmarks(
                vis_image, 
                hand_landmarks, 
                mp_hands.HAND_CONNECTIONS)
    
    # 모드 표시
    mode_text = "거울 모드: " + ("켜짐" if mirror_mode else "꺼짐")
    cv2.putText(vis_image, mode_text, (10, 30), 
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
    
    # 화면에 표시
    cv2.imshow('Full Body Neural Network Visualization', vis_image)
    
    # 키 입력 처리
    key = cv2.waitKey(5) & 0xFF
    if key == ord('q'):  # 'q' 키: 종료
        break
    elif key == ord('m'):  # 'm' 키: 거울 모드 전환
        mirror_mode = not mirror_mode
        print(f"거울 모드: {'켜짐' if mirror_mode else '꺼짐'}")

cap.release()
cv2.destroyAllWindows()
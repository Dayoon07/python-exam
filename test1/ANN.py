import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
import numpy as np
import matplotlib.pyplot as plt

# MNIST 데이터셋 로드
(x_train, y_train), (x_test, y_test) = keras.datasets.mnist.load_data()

# 데이터 전처리 (0~1 범위로 정규화)
x_train, x_test = x_train / 255.0, x_test / 255.0

# 신경망 모델 생성
model = keras.Sequential([
    layers.Flatten(input_shape=(28, 28)),  # 입력층 (28x28 이미지를 1D 배열로 변환)
    layers.Dense(128, activation='relu'),  # 은닉층
    layers.Dropout(0.2),  # 과적합 방지를 위한 드롭아웃
    layers.Dense(10, activation='softmax')  # 출력층 (10개의 클래스)
])

# 모델 컴파일
model.compile(optimizer='adam',
              loss='sparse_categorical_crossentropy',
              metrics=['accuracy'])

# 모델 학습
model.fit(x_train, y_train, epochs=5, validation_data=(x_test, y_test))

# 모델 평가
test_loss, test_acc = model.evaluate(x_test, y_test, verbose=2)
print(f"Test accuracy: {test_acc:.4f}")

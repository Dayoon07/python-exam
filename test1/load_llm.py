import tensorflow as tf
from tensorflow import keras
from keras.utils import custom_object_scope

# TransformerBlock 레이어를 커스텀 객체로 등록
from llm import TransformerBlock  # TransformerBlock이 정의된 모듈을 임포트

# 모델 불러오기
with custom_object_scope({'TransformerBlock': TransformerBlock}):
    model = keras.models.load_model("mdl.h5")

# 모델 구조를 딕셔너리 형식으로 출력
model_config = model.get_config()
print(model_config)

# pip install tensorflow==2.12.0
import tensorflow as tf
from tensorflow import keras
from keras.layers import Input, Embedding, Dense, MultiHeadAttention, LayerNormalization, Dropout
import numpy as np

# 1. Transformer 블록 정의
class TransformerBlock(keras.layers.Layer):
    def __init__(self, embed_dim, num_heads, ff_dim, rate=0.1):
        super(TransformerBlock, self).__init__()
        self.att = MultiHeadAttention(num_heads=num_heads, key_dim=embed_dim)
        self.ffn = keras.Sequential(
            [Dense(ff_dim, activation="relu"), Dense(embed_dim)]
        )
        self.layernorm1 = LayerNormalization(epsilon=1e-6)
        self.layernorm2 = LayerNormalization(epsilon=1e-6)
        self.dropout1 = Dropout(rate)
        self.dropout2 = Dropout(rate)

    def call(self, inputs, training):
        attn_output = self.att(inputs, inputs)
        attn_output = self.dropout1(attn_output, training=training)
        out1 = self.layernorm1(inputs + attn_output)

        ffn_output = self.ffn(out1)
        ffn_output = self.dropout2(ffn_output, training=training)
        return self.layernorm2(out1 + ffn_output)

# 2. 간단한 LLM 모델 정의
def build_model(vocab_size, max_len, embed_dim=128, num_heads=4, ff_dim=256):
    inputs = Input(shape=(max_len,))
    embedding_layer = Embedding(vocab_size, embed_dim)(inputs)
    transformer_block = TransformerBlock(embed_dim, num_heads, ff_dim)
    x = transformer_block(embedding_layer)
    x = Dense(vocab_size, activation="softmax")(x)

    model = keras.Model(inputs=inputs, outputs=x)
    return model

# 3. 하이퍼파라미터 설정
vocab_size = 10000  # 어휘 크기
max_len = 50  # 입력 시퀀스 길이
model = build_model(vocab_size, max_len)

# 4. 모델 컴파일 및 요약
model.compile(loss="sparse_categorical_crossentropy", optimizer="adam", metrics=["accuracy"])
model.summary()
model.save("mdl.h5")

"""
def chat():
print("안녕하세요! 대화를 시작하세요. ('exit' 입력 시 종료)")

while True:
    user_input = input("You: ")
    if user_input.lower() == 'exit':
        print("대화가 종료되었습니다.")
        break
    
    # 1. 사용자 입력을 처리 (토큰화 + 패딩)
    input_sequence = tokenizer.texts_to_sequences([user_input])
    input_sequence_padded = pad_sequences(input_sequence, padding='post', maxlen=50)
    
    # 2. 모델 예측
    output = model.predict(input_sequence_padded)
    
    # 3. 예측된 단어 출력
    predicted_index = output[0].argmax(axis=-1)
    predicted_word = tokenizer.index_word[predicted_index]
    
    print(f"Bot: {predicted_word}")

chat()
"""

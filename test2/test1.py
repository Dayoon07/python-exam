import tensorflow as tf
import numpy as numpy

키 = 168
신발 = 260

a = tf.Variable(0.1)
b = tf.Variable(0.2)


def lossFunc():
    predict_value = 키 * a + b
    return tf.square(신발 - predict_value)

opt = tf.keras.optimizers.Adam(learning_rate=0.1)

for i in range(300):
    opt.minimize(lossFunc, var_list=[a, b])
    print(a, b)



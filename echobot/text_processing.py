# encoding=utf-8
import jieba
import jieba.analyse
jieba.initialize()

def analyse_sentence(sentence):
    tokens = jieba.lcut(sentence)
    print(tokens)
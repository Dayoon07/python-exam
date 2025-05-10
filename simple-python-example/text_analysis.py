import argparse
from collections import Counter
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from nltk import ngrams
from konlpy.tag import Okt

# 영어 텍스트 단어 빈도 분석
# python text_analysis.py word_freq "문장" --language en

# 한국어 텍스트 단어 빈도 분석
# python text_analysis.py word_freq "문장" --language ko

# 영어 텍스트 키워드 추출
# python text_analysis.py keywords "문장"

# 한국어 텍스트 키워드 추출
# python text_analysis.py keywords "문장" --language ko

# 영어 N-그램 분석
# python text_analysis.py ngram "문장" --n 3 --language en

# 한국어 N-그램 분석
# python text_analysis.py ngram "뮨장" --n 2 --language ko


# 단어 빈도 분석 (영어와 한국어 모두 처리)
def word_frequency(text, language='en'):
    if language == 'ko':  # 한국어일 경우
        okt = Okt()
        words = okt.nouns(text)  # 명사만 추출
    else:  # 영어일 경우
        words = re.findall(r'\w+', text.lower())
    return Counter(words)

# 키워드 추출 (TF-IDF)
def extract_keywords(text, language='en'):
    if language == 'ko':  # 한국어일 경우
        okt = Okt()
        words = okt.nouns(text)  # 명사만 추출
        text = ' '.join(words)  # 명사만 포함된 텍스트로 변환
    vectorizer = TfidfVectorizer(stop_words='english' if language == 'en' else None)
    tfidf_matrix = vectorizer.fit_transform([text])
    feature_names = vectorizer.get_feature_names_out()
    scores = tfidf_matrix.sum(axis=0).A1
    return dict(zip(feature_names, scores))

# n-그램 분석
def ngram_analysis(text, n=2, language='en'):
    if language == 'ko':  # 한국어일 경우
        okt = Okt()
        words = okt.nouns(text)  # 명사만 추출
    else:  # 영어일 경우
        words = text.split()
    n_grams = ngrams(words, n)
    return dict(Counter(n_grams))

# 메인 함수
def main():
    parser = argparse.ArgumentParser(description="텍스트 분석 툴")
    parser.add_argument("command", choices=["word_freq", "keywords", "sentence_length", "ngram"],
                        help="분석할 명령어")
    parser.add_argument("text", help="분석할 텍스트")
    parser.add_argument("--n", type=int, default=2, help="n-그램에서 n값 (기본값: 2)")
    parser.add_argument("--language", choices=['en', 'ko'], default='en', help="언어 선택 ('en' 또는 'ko', 기본값: 'en')")

    args = parser.parse_args()

    if args.command == "word_freq":
        result = word_frequency(args.text, language=args.language)
    elif args.command == "keywords":
        result = extract_keywords(args.text, language=args.language)
    elif args.command == "sentence_length":
        result = sentence_length_analysis(args.text)
    elif args.command == "ngram":
        result = ngram_analysis(args.text, n=args.n, language=args.language)

    print(result)

if __name__ == "__main__":
    main()

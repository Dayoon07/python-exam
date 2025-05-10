import ollama

def generate_response(question):
    prompt = f"질문: {question}\n답변:"
    
    response = ollama.chat(
        model="deepseek-r1:8b",
        messages=[{"role": "user", "content": prompt}]
    )
    
    return response["message"]["content"]

def main():
    print("\n===== Ollama 기반 챗봇 (종료하려면 'q' 입력) =====\n")
    
    while True:
        question = input("질문: ")
        if question.lower() == 'q':
            print("프로그램을 종료합니다.")
            break
        
        response = generate_response(question)
        print(f"\n답변: {response}\n")

if __name__ == "__main__":
    main()

import os
import sys
from dotenv import load_dotenv
from openai import OpenAI

# 현재 파일의 부모의 부모 폴더(루트)를 경로에 추가 (main.py를 찾기 위함)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from main import get_db
except ImportError:
    # 혹시 에러가 난다면 경로를 직접 지정하는 방식
    print("main.py를 찾을 수 없습니다. 경로 설정을 확인하세요.")

# .env 파일 로드
load_dotenv()

# Upstage API 설정을 위한 클라이언트 초기화 
client = OpenAI(
    api_key=os.getenv("UPSTAGE_API_KEY"),
    base_url="https://api.upstage.ai/v1"
)

def get_today_todo_summary():
    """
    오늘 생성된 Todo 목록을 조회하여 AI로 요약하는 함수
    """
    # 1. DB 연결 및 오늘 날짜 데이터 조회 
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    # 오늘 날짜에 생성된 Todo 개수를 가져오는 쿼리
    query = "SELECT COUNT(*) as total FROM todo WHERE DATE(created_at) = CURDATE()"
    cursor.execute(query)
    row = cursor.fetchone()
    
    cursor.close()
    conn.close()
    
    total = row["total"] if row else 0

    # 2. LLM 프롬프트 설계 (Step 1-B 참고) 
    # 사용자가 친근하게 느낄 수 있도록 한국어 요약 요청
    prompt = f"""
    오늘 할 일이 총 {total}개 있습니다. 
    이 데이터를 바탕으로 오늘 할 일이 몇 개 남아있는지 알려주는 
    다정하고 친절한 요약 문장을 한국어로 한 문장만 만들어줘.
    
    예시: "오늘 할 일은 총 {total}개가 남아 있습니다. 하나씩 차근차근 해결해봐요!"
    """

    # 3. Solar 모델 호출 
    response = client.chat.completions.create(
        model="solar-pro2",
        messages=[
            {"role": "system", "content": "당신은 사용자의 업무를 도와주는 친절한 AI 비서입니다."},
            {"role": "user", "content": prompt}
        ],
    )

    summary_text = response.choices[0].message.content.strip()

    return {
        "total_count": total,
        "summary": summary_text
    }
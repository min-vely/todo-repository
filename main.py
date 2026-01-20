from fastapi import FastAPI, Request, HTTPException
import mysql.connector
from services.ai_agent import get_today_todo_summary

app = FastAPI()


try:
    from database import get_db
except ImportError:
    # 혹시 파일명이 database가 아닐 경우를 대비
    print("여전히 get_db를 찾을 수 없습니다. 파일명을 확인하세요.")


@app.post("/todos")
async def create_todo(request: Request):
    body = await request.json()
    content = body.get("content")

    if not content:
        raise HTTPException(status_code=400, detail="content is required")

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("INSERT INTO todo (content) VALUES (%s)", (content,))
    conn.commit()

    todo_id = cursor.lastrowid

    cursor.execute("SELECT id, content, created_at FROM todo WHERE id = %s", (todo_id,))
    row = cursor.fetchone()

    cursor.close()
    conn.close()

    return {"id": row[0], "content": row[1], "created_at": str(row[2])}


@app.get("/todos")
def get_todos():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT id, content, created_at FROM todo ORDER BY id DESC")
    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    return [{"id": r[0], "content": r[1], "created_at": str(r[2])} for r in rows]

# Step 3-A: Summary API 엔드포인트 생성 
@app.get("/todos/summary", status_code=200) # status_code를 명시해봅니다.
def get_summary_api():
    """
    오늘의 할 일 요약을 반환하는 API
    """
    try:
        print("Summary API 호출됨!") # 서버 터미널에 이 글자가 찍히는지 확인용
        result = get_today_todo_summary()
        return result
    except Exception as e:
        print(f"에러 발생: {e}") # 에러 내용을 터미널에 출력
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/todos/{todo_id}")
def delete_todo(todo_id: int):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM todo WHERE id = %s", (todo_id,))
    conn.commit()

    affected = cursor.rowcount

    cursor.close()
    conn.close()

    if affected == 0:
        raise HTTPException(status_code=404, detail="Todo not found")

    return {"message": "Todo deleted"}

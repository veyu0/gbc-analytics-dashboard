from fastapi import FastAPI
from fastapi.responses import RedirectResponse, HTMLResponse

app = FastAPI()

@app.get("/", response_class=HTMLResponse)
async def root():
    # Показываем ссылку на Streamlit-дэшборд
    html = """
    <html><head><title>Дашборд</title></head><body>
    <h2>Перейдите к аналитическому дашборду:</h2>
    <a href='/dashboard' target='_blank'>Открыть дашборд Streamlit</a>
    <br><br>
    <b>ИЛИ</b><br>
    <form action='/dashboard'>
        <button type='submit'>Перейти к дашборду</button>
    </form>
    </body></html>
    """
    return HTMLResponse(content=html)

@app.get("/dashboard")
async def dashboard_redirect():
    # Редирект на Streamlit, если он запущен на стандартном порту
    return RedirectResponse(url="http://172.19.0.2:8501")
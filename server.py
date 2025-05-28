from fastmcp import FastMCP, Context
import requests
from bs4 import BeautifulSoup
import os
from pydantic import BaseModel
import subprocess
import re
import json

# 서버 설정 구조를 Pydantic 모델로 정의
class ServerConfig(BaseModel):
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    MCP_PATH: str = "/mcp"
    # 필요한 다른 설정 옵션이 있다면 여기에 추가

# 환경 변수에서 MCP 경로를 읽어오거나, 기본값 "/mcp" 사용
# 이 부분은 Pydantic 모델에서 기본값을 제공하므로 필요 없을 수 있으나,
# 현재 코드 구조를 유지하기 위해 남겨둡니다.
mcp_path = os.environ.get("MCP_PATH", "/mcp")

# FastMCP 객체 생성 시 config_schema 인자로 Pydantic 모델 전달
mcp = FastMCP(
    "Dreamhack MCP",
    path=mcp_path,
    config_schema=ServerConfig,
    lazy_load=True  # 지연 로딩 활성화
)

# 세션 전역 관리
session = None

# -------------------- TOOLS --------------------

@mcp.tool()
def dreamhack_login(email: str, password: str) -> dict:
    """Dreamhack 로그인"""
    global session
    session = requests.Session()
    email_exist_resp = session.post("https://dreamhack.io/api/v1/auth/email-exist/", json={'email': email})
    if email_exist_resp.status_code != 200:
        return {"error": "Email existence check failed"}
    login_resp = session.post("https://dreamhack.io/api/v1/auth/login/", json={'email': email, 'password': password})
    if login_resp.status_code != 200:
        return {"error": "Login failed"}
    cookies = session.cookies.get_dict()
    if not cookies:
        return {"error": "No session cookies found"}
    return {"success": True, "cookies": cookies, "message": "Login successful"}

@mcp.tool()
def fetch_problems() -> dict:
    """문제 전체 목록 가져오기"""
    global session
    if not session:
        return {"error": "Not logged in"}
    problems = []
    page = 1
    while True:
        res = session.get(f"https://dreamhack.io/wargame?category=web&page={page}")
        soup = BeautifulSoup(res.text, "html.parser")
        all_rows = soup.select(".challenge-row")
        if not all_rows:
            break
        for row in all_rows:
            cat = row.select_one(".challenge-category")
            title = row.select_one(".title-text")
            link = row.select_one("a.title")
            if not (cat and title and link):
                continue
            level_img = row.select_one(".wargame-level")
            difficulty = "Unknown"
            if level_img and 'src' in level_img.attrs:
                src = level_img['src']
                for d in "12345":
                    if d in src:
                        difficulty = d
                        break
            problems.append({
                "title": title.text.strip(),
                "category": cat.text.strip(),
                "difficulty": difficulty,
                "link": "https://dreamhack.io" + link["href"]
            })
        page += 1
    return {"success": True, "total_problems": len(problems), "problems": problems}

@mcp.tool()
def fetch_problems_by_difficulty(difficulty: str = "all") -> dict:
    """난이도별 문제 목록 가져오기"""
    global session
    if not session:
        return {"error": "Not logged in"}
    problems = []
    page = 1
    difficulty_map = {'beginner': 'beginner', '1': '1', '2': '2', '3': '3', '4': '4', '5': '5'}
    while True:
        url = f"https://dreamhack.io/wargame?category=web&page={page}"
        if difficulty != 'all':
            url += f"&difficulty={difficulty_map.get(difficulty, difficulty)}"
        res = session.get(url)
        soup = BeautifulSoup(res.text, "html.parser")
        all_rows = soup.select(".challenge-row")
        if not all_rows:
            break
        for row in all_rows:
            cat = row.select_one(".challenge-category")
            title = row.select_one(".title-text")
            link = row.select_one("a.title")
            if not (cat and title and link):
                continue
            current_difficulty = difficulty if difficulty != 'all' else "Unknown"
            problems.append({
                "title": title.text.strip(),
                "category": cat.text.strip(),
                "difficulty": current_difficulty,
                "link": "https://dreamhack.io" + link["href"]
            })
        page += 1
    return {"success": True, "total_problems": len(problems), "difficulty": difficulty, "problems": problems}

@mcp.tool()
def download_challenge(url: str, title: str) -> dict:
    """문제 파일 다운로드 및 압축 해제"""
    global session
    if not session:
        return {"error": "Not logged in"}
    if not url or not title:
        return {"error": "url and title required"}
    if not url.startswith('http'):
        url = "https://dreamhack.io" + url
    res = session.get(url)
    soup = BeautifulSoup(res.text, "html.parser")
    download_links = soup.select(".challenge-download")
    if not download_links:
        return {"error": "No download links found"}
    files = []
    downloaded_urls = set()
    safe_title = re.sub(r'[<>:"/\\|?*]', '_', title)
    for link in download_links:
        href = link.get('href')
        if not href:
            continue
        file_url = href if href.startswith('http') else "https://dreamhack.io" + href
        if file_url in downloaded_urls:
            continue
        downloaded_urls.add(file_url)
        file_name = href.split('/')[-1].split('?')[0]
        file_res = session.get(file_url)
        if file_res.status_code == 200:
            problem_dir = safe_title
            if not os.path.exists(problem_dir):
                os.makedirs(problem_dir)
            file_path = os.path.join(problem_dir, file_name)
            with open(file_path, 'wb') as f:
                f.write(file_res.content)
            files.append(file_path)
            if file_name.endswith('.zip'):
                import zipfile
                with zipfile.ZipFile(file_path, 'r') as zip_ref:
                    zip_ref.extractall(problem_dir)
                os.remove(file_path)
                files.remove(file_path)
                extracted_files = os.listdir(problem_dir)
                files.extend([os.path.join(problem_dir, f) for f in extracted_files])
    return {"success": True, "title": safe_title, "files": files}

@mcp.tool()
def deploy_challenge(challenge_dir: str) -> dict:
    """문제 디렉토리에서 Docker 또는 app.py로 배포"""
    try:
        problem_dirs = [d for d in os.listdir(challenge_dir) if os.path.isdir(os.path.join(challenge_dir, d)) and d != '__pycache__']
        if not problem_dirs:
            return {"error": "No problem directory found"}
        problem_dir = os.path.join(challenge_dir, problem_dirs[-1])
        if os.path.exists(os.path.join(problem_dir, 'Dockerfile')):
            image_name = f"challenge-{os.path.basename(problem_dir)}"
            docker_path = problem_dir.replace('\\', '/')
            build_cmd = f'docker build -t {image_name} "{docker_path}"'
            subprocess.run(build_cmd, shell=True, check=True)
            stop_cmd = f"docker stop {image_name} 2>nul || true"
            rm_cmd = f"docker rm {image_name} 2>nul || true"
            subprocess.run(stop_cmd, shell=True)
            subprocess.run(rm_cmd, shell=True)
            run_cmd = f"docker run -d --name {image_name} -p 8000:8000 {image_name}"
            subprocess.run(run_cmd, shell=True, check=True)
            ps_cmd = f"docker ps --filter name={image_name}"
            result = subprocess.run(ps_cmd, shell=True, capture_output=True, text=True)
            if image_name not in result.stdout:
                return {"error": "Container failed to start"}
            return {"success": True, "message": f"Challenge deployed at http://localhost:8000", "image_name": image_name, "deployment_type": "docker"}
        elif os.path.exists(os.path.join(problem_dir, 'app.py')):
            app_path = os.path.join(problem_dir, 'app.py')
            if os.path.exists(os.path.join(problem_dir, 'requirements.txt')):
                subprocess.run(f"pip install -r {os.path.join(problem_dir, 'requirements.txt')}", shell=True, check=True)
            else:
                subprocess.run("pip install flask", shell=True, check=True)
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                process = subprocess.Popen(['python', app_path], startupinfo=startupinfo, creationflags=subprocess.CREATE_NEW_CONSOLE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=problem_dir)
            else:
                process = subprocess.Popen(['python3', app_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=problem_dir)
            if process.poll() is not None:
                stdout, stderr = process.communicate()
                return {"error": f"Failed to start app.py. Exit code: {process.returncode}"}
            return {"success": True, "message": f"Challenge deployed at http://localhost:8000", "process_id": process.pid, "deployment_type": "python"}
        else:
            return {"error": "Neither Dockerfile nor app.py found in challenge directory"}
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
def stop_challenge(deployment_type: str, image_name: str = None, process_id: int = None) -> dict:
    """배포된 문제 서버 중지"""
    if deployment_type == 'docker':
        if not image_name:
            return {"error": "image_name is required"}
        stop_cmd = f"docker stop {image_name}"
        rm_cmd = f"docker rm {image_name}"
        subprocess.run(stop_cmd, shell=True)
        subprocess.run(rm_cmd, shell=True)
        return {"success": True, "message": f"Docker container {image_name} stopped and removed."}
    elif deployment_type == 'python':
        if not process_id:
            return {"error": "process_id is required"}
        if os.name == 'nt':
            kill_cmd = f"taskkill /PID {process_id} /F"
        else:
            kill_cmd = f"kill -9 {process_id}"
        subprocess.run(kill_cmd, shell=True)
        return {"success": True, "message": f"Python process {process_id} killed."}
    else:
        return {"error": "Unknown deployment_type"}

@mcp.tool()
def submit_flag(url: str, flag: str) -> dict:
    """문제의 flag 제출"""
    global session
    if not session:
        return {"error": "Not logged in"}

    try:
        if not url or not flag:
            return {"error": "url and flag are required"}

        # URL이 상대 경로인 경우 절대 경로로 변환
        if not url.startswith('http'):
            url = "https://dreamhack.io" + url

        # 문제 페이지 접근
        res = session.get(url)
        if res.status_code != 200:
            return {"error": f"Failed to access challenge page: {res.status_code}"}

        # CSRF 토큰 추출
        soup = BeautifulSoup(res.text, "html.parser")
        csrf_token = soup.find('meta', {'name': 'csrf-token'})
        if not csrf_token:
            return {"error": "CSRF token not found"}

        # Flag 제출
        submit_url = f"{url}/submit"
        headers = {
            'X-CSRFToken': csrf_token['content'],
            'Content-Type': 'application/json',
            'Referer': url
        }
        
        submit_data = {
            'flag': flag
        }
        
        submit_resp = session.post(submit_url, json=submit_data, headers=headers)
        
        if submit_resp.status_code == 200:
            result = submit_resp.json()
            return {
                "success": True,
                "message": result.get('message', 'Flag submitted successfully'),
                "result": result
            }
        else:
            return {
                "error": f"Failed to submit flag: {submit_resp.status_code}",
                "details": submit_resp.text
            }

    except Exception as e:
        return {"error": str(e)}

# -------------------- PROMPTS --------------------

@mcp.prompt()
def login_prompt(email: str) -> str:
    return f"Dreamhack 계정 {email}로 로그인 시도 중입니다."

@mcp.prompt()
def problem_summary_prompt(title: str, category: str, difficulty: str) -> str:
    return f"문제: {title}\n카테고리: {category}\n난이도: {difficulty}\n이 문제를 풀어보시겠습니까?"

@mcp.prompt()
def deploy_prompt(title: str) -> str:
    return f"문제 '{title}'를 서버에 배포합니다. 계속하시겠습니까?"

@mcp.prompt()
def submit_flag_prompt(url: str) -> str:
    return f"문제 페이지 {url}에 flag를 제출합니다. 계속하시겠습니까?"

# -------------------- RESOURCES --------------------

@mcp.resource("problems://all")
def all_problems_resource():
    """전체 문제 목록을 리소스로 제공"""
    return fetch_problems()["problems"]

@mcp.resource("problems://{difficulty}")
def problems_by_difficulty_resource(difficulty: str):
    """난이도별 문제 목록 리소스"""
    return fetch_problems_by_difficulty(difficulty)["problems"]

@mcp.resource("challenge://{title}/files")
def challenge_files_resource(title: str):
    """다운로드된 문제 파일 목록 리소스"""
    safe_title = re.sub(r'[<>:"/\\|?*]', '_', title)
    if not os.path.exists(safe_title):
        return []
    return [os.path.join(safe_title, f) for f in os.listdir(safe_title)]

@mcp.resource("health")
def health_check():
    """서버 상태 확인을 위한 헬스 체크 엔드포인트"""
    return {"status": "healthy"}

if __name__ == "__main__":
    # 환경 변수에서 호스트와 포트 값을 읽어오거나, 기본값을 사용
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", 8000))

    # fastmcp 서버 실행 (환경 변수에서 읽은 호스트/포트 사용)
    mcp.run(
        transport="streamable-http",
        host=host,
        port=port,
        lazy_load=True  # 지연 로딩 활성화
    ) 

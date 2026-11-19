import sqlite3
import time
import requests
from bs4 import BeautifulSoup

# --- 1. データベースの初期化 ---
def init_db(db_name="github_google.db"):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    # テーブル作成（すでに存在する場合はスキップ）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS repositories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            language TEXT,
            stars TEXT
        )
    ''')
    conn.commit()
    conn.close()

# --- 2. Googleのリポジトリ一覧をスクレイピング ---
def scrape_google_repos():
    # GoogleのGitHubリポジトリ一覧URL
    url = "https://github.com/orgs/google/repositories"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    print("スクレイピングを開始します...")
    response = requests.get(url, headers=headers)
    
    # マナーを守るための待機時間（指示要件）
    time.sleep(1)

    if response.status_code != 200:
        print(f"取得に失敗しました。ステータスコード: {response.status_code}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    repos_data = []

    # GitHubのHTML構造に合わせて要素を取得（※GitHubの仕様変更でクラス名が変わることがあります）
    # リポジトリリストの各カードを取得
    repo_list = soup.find_all("li", class_="Box-row")

    for repo in repo_list:
        # 1. リポジトリ名
        name_tag = repo.find("a", itemprop="name codeRepository")
        repo_name = name_tag.text.strip() if name_tag else "N/A"

        # 2. 主要言語
        lang_tag = repo.find("span", itemprop="programmingLanguage")
        language = lang_tag.text.strip() if lang_tag else "Unknown"

        # 3. スター数
        star_tag = repo.find("a", class_="Link--muted")
        stars = star_tag.text.strip() if star_tag else "0"

        repos_data.append((repo_name, language, stars))

    return repos_data

# --- 3. データをDBへ保存 ---
def save_to_db(repos_data, db_name="github_google.db"):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    
    # 既存データをクリアしたい場合はリセット（任意）
    cursor.execute("DELETE FROM repositories")
    
    cursor.executemany('''
        INSERT INTO repositories (name, language, stars)
        VALUES (?, ?, ?)
    ''', repos_data)
    
    conn.commit()
    conn.close()
    print(f"{len(repos_data)} 件のデータをDBに保存しました。")

# --- 4. SELECT文でデータを表示 ---
def display_stored_repos(db_name="github_google.db"):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, name, language, stars FROM repositories")
    rows = cursor.fetchall()
    
    print("\n=== 保存されたリポジトリ情報 (SELECT結果) ===")
    print(f"{'ID':<4} | {'リポジトリ名':<30} | {'言語':<12} | {'スター数':<8}")
    print("-" * 60)
    for row in rows:
        print(f"{row[0]:<4} | {row[1]:<30} | {row[2]:<12} | {row[3]:<8}")
        
    conn.close()

if __name__ == "__main__":
    DB_NAME = "github_google.db"
    init_db(DB_NAME)
    data = scrape_google_repos()
    if data:
        save_to_db(data, DB_NAME)
        display_stored_repos(DB_NAME)
import sqlite3
import time
import re
import requests
from bs4 import BeautifulSoup

# --- 1. データベースの初期化 ---
def init_db(db_name="github_google.db"):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
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
def scrape_google_repos(max_pages=3):
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9"
    }

    repos_data = []
    seen_names = set()

    for page in range(1, max_pages + 1):
        url = f"https://github.com/orgs/google/repositories?page={page}"
        print(f"{page}ページ目を取得中: {url}")

        response = requests.get(url, headers=headers)
        time.sleep(1)  # 要件：1秒待機

        if response.status_code != 200:
            print(f"取得失敗 (ステータスコード: {response.status_code})")
            break

        soup = BeautifulSoup(response.text, "html.parser")

        # '/google/リポジトリ名' へのリンクをすべて探索
        repo_links = soup.find_all("a", href=re.compile(r"^/google/[^/]+$"))

        page_count = 0
        for link in repo_links:
            repo_name = link.get_text(strip=True)
            # ナビゲーション等の空リンクや重複・組織トップを除外
            if not repo_name or repo_name in seen_names or repo_name == "google":
                continue

            # リポジトリの親ブロック（li または行コンテナ）を遡って取得
            container = link.find_parent("li") or link.find_parent("div", class_=re.compile(r"Box-row|ListItem"))
            if not container:
                continue

            seen_names.add(repo_name)
            page_count += 1

            # 言語の取得（GitHubの言語バッジ用クラスまたは属性から取得）
            lang_tag = (
                container.find("span", attrs={"itemprop": "programmingLanguage"})
                or container.find("span", class_=re.compile(r"repo-language-color"))
            )
            if lang_tag:
                # 色丸スパンの隣に言語名テキストがある場合の対応
                if lang_tag.get_text(strip=True):
                    language = lang_tag.get_text(strip=True)
                elif lang_tag.next_sibling:
                    language = str(lang_tag.next_sibling).strip()
                else:
                    language = "Unknown"
            else:
                language = "Unknown"

            # スター数の取得（/stargazers へのリンクから取得）
            star_tag = container.find("a", href=re.compile(r"/stargazers$"))
            stars = star_tag.get_text(strip=True) if star_tag else "0"

            repos_data.append((repo_name, language, stars))

        print(f"  -> {page_count} 件抽出")
        if page_count == 0:
            break

    return repos_data

# --- 3. データをDBへ保存 ---
def save_to_db(repos_data, db_name="github_google.db"):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    cursor.execute("DELETE FROM repositories")
    cursor.executemany('''
        INSERT INTO repositories (name, language, stars)
        VALUES (?, ?, ?)
    ''', repos_data)

    conn.commit()
    conn.close()
    print(f"\n合計 {len(repos_data)} 件のデータをDBに保存しました。")

# --- 4. SELECT文でデータを表示 ---
def display_stored_repos(db_name="github_google.db"):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    cursor.execute("SELECT id, name, language, stars FROM repositories")
    rows = cursor.fetchall()

    print("\n=== 保存されたリポジトリ情報 (SELECT結果) ===")
    print(f"{'ID':<4} | {'リポジトリ名':<30} | {'言語':<15} | {'スター数':<8}")
    print("-" * 65)
    for row in rows:
        print(f"{row[0]:<4} | {row[1]:<30} | {row[2]:<15} | {row[3]:<8}")

    conn.close()

if __name__ == "__main__":
    DB_NAME = "github_google.db"
    init_db(DB_NAME)
    data = scrape_google_repos(max_pages=3)  # 必要に応じてページ数を変更
    if data:
        save_to_db(data, DB_NAME)
        display_stored_repos(DB_NAME)
    else:
        print("データが取得できませんでした。")
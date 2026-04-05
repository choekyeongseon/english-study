#!/usr/bin/env python3
"""
Confluence → GitHub 동기화 스크립트

사용법:
  1. Atlassian API 토큰 생성: https://id.atlassian.com/manage-profile/security/api-tokens
  2. 실행:
     ATLASSIAN_EMAIL=your@email.com \
     ATLASSIAN_TOKEN=your-api-token \
     GITHUB_TOKEN=ghp_xxx \
     python3 sync_confluence_to_github.py
"""

import os
import sys
import json
import base64
import subprocess
import urllib.request
import urllib.error

# ═══════════════════════════════════════════════════════
# Configuration
# ═══════════════════════════════════════════════════════

CONFLUENCE_BASE = "https://pms-innogrid.atlassian.net/wiki"
GITHUB_REPO = "choekyeongseon/english-study"
MAIN_PAGE_ID = "1790443631"

# Page ID → file path mapping
PAGE_MAP = {
    "1790541952": "lessons/2026-03-12-food-and-mood.md",
    "1799454735": "lessons/2026-03-17-public-behavior.md",
    "1815183418": "lessons/2026-03-19-cashless-society.md",
    "1828782162": "lessons/2026-03-24-job-interviews.md",
    "1831698555": "lessons/2026-03-26-frozen-food.md",
    "1851293728": "lessons/2026-04-01-patterns.md",
    "1856503996": "lessons/2026-04-02-work-hours.md",
    "1795752306": "guides/conversation-guides.md",
    "1796603984": "guides/practice-guides.md",
    "1796833283": "reference/grammar-notes.md",
    "1796767749": "reference/expressions-vocabulary.md",
}

# ═══════════════════════════════════════════════════════
# Functions
# ═══════════════════════════════════════════════════════

def get_env(key):
    val = os.environ.get(key)
    if not val:
        print(f"❌ 환경변수 {key}가 설정되지 않았습니다.")
        sys.exit(1)
    return val


def fetch_confluence_page(page_id, email, token):
    """Confluence REST API v2로 페이지를 마크다운 형태로 가져옴"""
    url = f"{CONFLUENCE_BASE}/api/v2/pages/{page_id}?body-format=export_view"
    
    # Try storage format first, then convert
    # Actually use the v1 API with expand=body.export_view for better markdown
    url_v1 = (
        f"{CONFLUENCE_BASE}/rest/api/content/{page_id}"
        f"?expand=body.export_view,body.storage"
    )
    
    # Use v2 with body-format=atlas_doc_format for structured content
    url_v2 = f"{CONFLUENCE_BASE}/api/v2/pages/{page_id}?body-format=storage"
    
    credentials = base64.b64encode(f"{email}:{token}".encode()).decode()
    
    req = urllib.request.Request(url_v2)
    req.add_header("Authorization", f"Basic {credentials}")
    req.add_header("Accept", "application/json")
    
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
            title = data.get("title", "")
            body_storage = data.get("body", {}).get("storage", {}).get("value", "")
            return title, body_storage
    except urllib.error.HTTPError as e:
        print(f"  ❌ HTTP {e.code}: {e.reason}")
        return None, None


def convert_storage_to_markdown(html_content):
    """
    Confluence storage format (HTML) → Markdown 변환
    간단한 변환기. 더 정확한 변환이 필요하면 pypandoc 사용 권장.
    """
    try:
        # Try using pandoc if available
        result = subprocess.run(
            ["pandoc", "-f", "html", "-t", "markdown", "--wrap=none"],
            input=html_content,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            return result.stdout
    except FileNotFoundError:
        pass
    
    # Fallback: basic HTML to markdown conversion
    import re
    text = html_content
    # Headers
    for i in range(6, 0, -1):
        text = re.sub(f"<h{i}[^>]*>(.*?)</h{i}>", f"{'#' * i} \\1\n", text, flags=re.S)
    # Bold
    text = re.sub(r"<strong>(.*?)</strong>", r"**\1**", text, flags=re.S)
    # Italic
    text = re.sub(r"<em>(.*?)</em>", r"*\1*", text, flags=re.S)
    # Links
    text = re.sub(r'<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>', r"[\2](\1)", text, flags=re.S)
    # List items
    text = re.sub(r"<li>(.*?)</li>", r"* \1", text, flags=re.S)
    # Paragraphs
    text = re.sub(r"<p>(.*?)</p>", r"\1\n\n", text, flags=re.S)
    # Remove remaining tags
    text = re.sub(r"<[^>]+>", "", text)
    # Clean up whitespace
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def sync_all_pages(email, token, repo_dir):
    """모든 Confluence 페이지를 가져와서 로컬 파일에 저장"""
    print(f"📥 Fetching {len(PAGE_MAP)} pages from Confluence...")
    
    for page_id, filepath in PAGE_MAP.items():
        print(f"\n  📄 Fetching page {page_id} → {filepath}")
        title, body = fetch_confluence_page(page_id, email, token)
        
        if body is None:
            print(f"  ⚠️  Skipped (fetch failed)")
            continue
        
        # Convert to markdown
        markdown = convert_storage_to_markdown(body)
        
        # Add title as H1 if not present
        if not markdown.startswith("# "):
            markdown = f"# {title}\n\n{markdown}"
        
        # Write to file
        full_path = os.path.join(repo_dir, filepath)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(markdown.rstrip() + "\n")
        
        lines = markdown.count("\n") + 1
        print(f"  ✅ Written {lines} lines")
    
    print(f"\n✅ All pages fetched!")


def git_push(repo_dir, github_token):
    """변경사항을 GitHub에 push"""
    os.chdir(repo_dir)
    
    subprocess.run(["git", "add", "-A"], check=True)
    
    # Check if there are changes
    result = subprocess.run(
        ["git", "status", "--porcelain"], capture_output=True, text=True
    )
    
    if not result.stdout.strip():
        print("ℹ️  No changes to push.")
        return
    
    subprocess.run(
        ["git", "commit", "-m", 
         "🔄 Sync: Confluence → GitHub (full content update)\n\n"
         "모든 페이지를 Confluence 원본에서 재동기화"],
        check=True,
    )
    
    remote_url = f"https://choekyeongseon:{github_token}@github.com/{GITHUB_REPO}.git"
    subprocess.run(
        ["git", "remote", "set-url", "origin", remote_url],
        check=True,
    )
    subprocess.run(["git", "push", "origin", "main"], check=True)
    print("✅ Pushed to GitHub!")


# ═══════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════

if __name__ == "__main__":
    email = get_env("ATLASSIAN_EMAIL")
    token = get_env("ATLASSIAN_TOKEN")
    github_token = get_env("GITHUB_TOKEN")
    
    # Determine repo directory
    repo_dir = os.environ.get("REPO_DIR", os.getcwd())
    
    print("═" * 50)
    print("  Confluence → GitHub Sync")
    print("═" * 50)
    print(f"  Confluence: {CONFLUENCE_BASE}")
    print(f"  GitHub: {GITHUB_REPO}")
    print(f"  Repo dir: {repo_dir}")
    print("═" * 50)
    
    # Fetch all pages
    sync_all_pages(email, token, repo_dir)
    
    # Push to GitHub
    git_push(repo_dir, github_token)
    
    print("\n🎉 Done!")

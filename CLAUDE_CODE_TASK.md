# Claude Code 작업 지시서

아래 내용을 Claude Code에 그대로 붙여넣으세요.

---

## 프롬프트 (복사해서 붙여넣기)

```
GitHub 레포지토리 choekyeongseon/english-study 에 Confluence 영어 학습 내용을 전체 동기화해야 해.

## 현재 상황
- GitHub 레포: https://github.com/choekyeongseon/english-study
- 레포에 파일은 있지만, 내용이 많이 누락/축약되어 있어
- Confluence 원본의 완전한 내용으로 모든 파일을 덮어써야 함

## 작업 방법
1. 먼저 레포를 clone해
2. Confluence REST API v2를 사용해서 아래 11개 페이지의 마크다운 body를 가져와
3. 각 body를 해당 파일 경로에 그대로 저장해
4. commit하고 push해

## Confluence API 정보
- Base URL: https://pms-innogrid.atlassian.net/wiki
- API endpoint: GET /api/v2/pages/{pageId}?body-format=atlas_doc_format
- 인증: Basic Auth (email:api-token)
- 내 이메일: (실행 전에 ATLASSIAN_EMAIL 환경변수로 설정)
- API 토큰: (실행 전에 ATLASSIAN_TOKEN 환경변수로 설정)
  - 토큰 발급: https://id.atlassian.com/manage-profile/security/api-tokens

## 페이지 ID → 파일 경로 매핑

| Page ID | 파일 경로 |
|---------|----------|
| 1790541952 | lessons/2026-03-12-food-and-mood.md |
| 1799454735 | lessons/2026-03-17-public-behavior.md |
| 1815183418 | lessons/2026-03-19-cashless-society.md |
| 1828782162 | lessons/2026-03-24-job-interviews.md |
| 1831698555 | lessons/2026-03-26-frozen-food.md |
| 1851293728 | lessons/2026-04-01-patterns.md |
| 1856503996 | lessons/2026-04-02-work-hours.md |
| 1795752306 | guides/conversation-guides.md |
| 1796603984 | guides/practice-guides.md |
| 1796833283 | reference/grammar-notes.md |
| 1796767749 | reference/expressions-vocabulary.md |

## 페이지 가져오는 방법

각 페이지를 이렇게 가져와:

curl -s -u "$ATLASSIAN_EMAIL:$ATLASSIAN_TOKEN" \
  "https://pms-innogrid.atlassian.net/wiki/api/v2/pages/{pageId}?body-format=storage" \
  -H "Accept: application/json"

응답의 body.storage.value 필드가 HTML인데, 이걸 마크다운으로 변환해서 저장해.
pandoc이 있으면 `pandoc -f html -t markdown --wrap=none`으로 변환.
없으면 `pip install markdownify`한 후 Python markdownify 라이브러리 사용.

## 또는 더 간단한 방법

Confluence REST API v1도 사용 가능:

curl -s -u "$ATLASSIAN_EMAIL:$ATLASSIAN_TOKEN" \
  "https://pms-innogrid.atlassian.net/wiki/rest/api/content/{pageId}?expand=body.export_view" \
  -H "Accept: application/json"

body.export_view.value에 깨끗한 HTML이 나옴.

## Git 정보
- GitHub token: GITHUB_TOKEN 환경변수 사용
- remote URL: https://{GITHUB_TOKEN}@github.com/choekyeongseon/english-study.git
- branch: main
- commit message: "🔄 Full sync: Confluence → GitHub (원본 전체 내용 동기화)"

## README.md는 건드리지 마
README.md와 prompts/ 폴더의 파일들은 그대로 유지해.
lessons/, guides/, reference/ 폴더의 .md 파일만 덮어써.

## 주의사항
- 각 파일의 첫 줄은 `# 페이지제목` 형태의 H1이어야 해
- 마크다운 테이블이 깨지지 않게 주의해
- 한국어/영어 혼합 콘텐츠가 많으니 인코딩(UTF-8) 주의
- Confluence의 이모지(📌📚💬⚠️❓ 등)도 그대로 유지해
```

---

## 실행 전 준비사항

1. **Atlassian API 토큰 발급**
   - https://id.atlassian.com/manage-profile/security/api-tokens 접속
   - "Create API token" 클릭
   - 토큰 복사

2. **환경변수 설정**
   ```bash
   export ATLASSIAN_EMAIL="your-email@innogrid.com"
   export ATLASSIAN_TOKEN="your-atlassian-api-token"
   export GITHUB_TOKEN="YOUR_GITHUB_TOKEN_HERE"
   ```

3. **Claude Code 실행**
   ```bash
   cd ~/your-workspace
   claude
   ```
   그리고 위 프롬프트를 붙여넣으면 됩니다.

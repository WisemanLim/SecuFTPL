# impl/16th 시험 시나리오 — 데이터셋 고도화 (수집·검증·증강, 문서 조사 상세 반영)

요구 5건: ①문서 파일(PDF/DOCX 등) 수집 ②사용자 디렉토리 선택 ③URL 수집 정의
④UI 절차 재배치(채널→수집→증강) ⑤증강 자동 추천 + 역번역(ko→en→ko).

| # | 케이스 | 방법 | 기대 |
|---|---|---|---|
| 1 | 문서 텍스트 추출 | txt/md/html(script 제거)/docx | 본문 추출 (pdf 는 pypdf — 텍스트 레이어 전제) |
| 2 | 주석 대기 레코드 | `build_document_record` | task 지시 프레임 + `needs_annotation` assistant, 빈 문서 거부 |
| 3 | 파일 라우팅 | `collect_file` | 정형(jsonl/json) vs 문서(5종) 분기, 미지원 확장자 거부 |
| 4 | URL 수집 정의 | HTML 응답 | 본문 추출→주석 대기 레코드, JSON/JSONL=레코드 (자동 판별) |
| 5 | 치환 후보 추천 | 빈도+동의어 사전 | 아파치(빈도3)→nginx/IIS, 사전 매칭 항목만 |
| 6 | 역번역 | fake translator | `-bt-1` lineage·augmented, CVE/T-ID 복원, assistant 불변 |
| 7 | 역번역 백엔드 미가용 | Ollama 미기동 | 503 + 안내 |
| 8 | 문서 업로드 E2E | txt 업로드→승인→추천 | queued·needs_annotation·추천 응답 |
| 9 | UI 절차 | /datasets | ①용도→②채널 라디오→③수집→④증강(추천 버튼·역번역), 사용자 디렉토리(webkitdirectory) |
| 10 | 회귀 | pytest+ruff+build | 전건 통과 |

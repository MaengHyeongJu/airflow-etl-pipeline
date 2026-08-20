# Airflow ETL 포트폴리오 프로젝트

가상 센서/로그 데이터 → **Apache Airflow** DAG(수집 → 정제 → 적재) → **PostgreSQL** 데이터마트 → **Vue 3 + PrimeVue** 관리자 대시보드.

## 스택

| 영역 | 기술 |
|---|---|
| 오케스트레이션 | Apache Airflow 3.3.1, Docker Compose, LocalExecutor |
| 데이터마트 | PostgreSQL 16 (스테이징 + 차원모델 마트) |
| 백엔드 API | FastAPI + SQLAlchemy |
| 프런트엔드 | Vue 3 + TypeScript + PrimeVue 4 (Sakai 스타일 어드민 레이아웃, 직접 구현) |

LocalExecutor를 선택한 이유: 단일 노드에서 도는 포트폴리오 프로젝트 규모(하루 ~12개 태스크)에 Celery+Redis+worker 조합은 과함. 확장이 필요하면 CeleryExecutor + Redis로 교체하는 경로를 문서화하는 선에서 의도적으로 스코프를 좁힘.

## 아키텍처

```
generator (Python)  --writes-->  data/raw/{sensors,logs}/dt=YYYY-MM-DD/*.jsonl
        |
        v
Airflow DAG (etl_pipeline): discover -> clean -> load staging -> upsert dims
        -> merge facts -> build daily aggregates -> data quality checks
        |
        v
Postgres `datamart` (staging.* / mart.*)
        |
        v
FastAPI (dashboard_reader, SELECT-only)  <--  Vue/PrimeVue dashboard
```

## 빠른 시작

```bash
cp .env.example .env
# .env를 열어 AIRFLOW_UID(= `id -u`), AIRFLOW__CORE__FERNET_KEY, AIRFLOW__API__SECRET_KEY,
# AIRFLOW__API_AUTH__JWT_SECRET 값을 채운다.
#   Fernet key: python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
#   나머지 secret: python3 -c "import secrets; print(secrets.token_hex(32))"

docker compose up -d --build

# DAG가 뜨면 (http://localhost:8080, admin/admin) 몇 주치 백필해서 대시보드에 보여줄 데이터 확보
docker compose exec airflow-scheduler airflow dags backfill etl_pipeline \
  -s 2026-08-01 -e 2026-08-19

open http://localhost:8081   # 대시보드
open http://localhost:8000/docs  # API 문서
```

## 디렉터리

- `generator/` — 가상 센서/로그 데이터 생성기 (Airflow와 독립적으로 실행/테스트 가능)
- `airflow/` — DAG, ETL 헬퍼(`include/etl`), SQL(`include/sql`)
- `postgres/init/` — `airflow`/`datamart` DB 및 스키마/롤 생성 스크립트
- `backend/` — FastAPI (읽기 전용, `dashboard_reader` 롤로 접속)
- `frontend/` — Vue 3 + TS + PrimeVue 대시보드

## 알려진 환경 이슈 (Docker Desktop + WSL2)

`airflow backfill create`를 `--max-active-runs`를 3~4 이상으로 걸고 여러 날짜를 동시에 처음 실행하면, Docker Desktop의 WSL2 바인드 마운트(`./airflow/logs`)가 컨테이너-호스트 간 뷰가 어긋나며 로그 폴더 생성이 간헐적으로 `Permission denied`로 실패하는 현상이 관찰됨(Airflow/DAG 코드 문제 아님). 재현되면:

1. `docker compose restart airflow-scheduler airflow-dag-processor`로 마운트를 새로고침
2. 실패한 날짜만 `--reprocess-behavior failed --max-active-runs 1`로 재실행(동시성 1이면 재발하지 않음)

## 향후 과제

- 백엔드 API 인증(API key/JWT) 추가
- CeleryExecutor + Redis로 확장 (다중 워커가 필요해질 경우)

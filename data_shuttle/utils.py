from typing import Dict, Tuple, Generator, Iterable
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.engine import Engine, Row


def create_engine_from_config(cfg: Dict, connect_timeout: int | None = None) -> Engine:
    db_type = (cfg.get("db_type") or "").lower()
    host = cfg.get("host")
    port = cfg.get("port")
    svc  = cfg.get("service_or_db", "")
    user = cfg.get("user")
    pw   = cfg.get("password")

    if db_type.startswith("oracle"):
        # 예) oracle+oracledb://user:pw@host:1521/?service_name=ORCL
        url = f"oracle+oracledb://{user}:{pw}@{host}:{port}/?service_name={svc}"
        engine = create_engine(url, pool_pre_ping=True)
    elif db_type.startswith("postgre"):
        # 예) postgresql+psycopg://user:pw@host:5432/dbname
        if connect_timeout and connect_timeout > 0:
            url = f"postgresql+psycopg://{user}:{pw}@{host}:{port}/{svc}?connect_timeout={connect_timeout}"
        else:
            url = f"postgresql+psycopg://{user}:{pw}@{host}:{port}/{svc}"
        engine = create_engine(url, pool_pre_ping=True)
    else:
        raise ValueError(f"지원하지 않는 DB 타입: {cfg.get('db_type')}")

    return engine


def test_connection(cfg: Dict, timeout: int = 3) -> Tuple[bool, str]:
    """
    입력된 cfg로 실제 연결을 시도하여 (성공 여부, 상세메시지) 반환합니다.
    - Oracle: SELECT 1 FROM DUAL
    - Postgres: SELECT 1
    """
    try:
        engine = create_engine_from_config(cfg, connect_timeout=timeout)
        test_sql = text("SELECT 1")
        if (cfg.get("db_type") or "").lower().startswith("oracle"):
            test_sql = text("SELECT 1 FROM DUAL")

        with engine.connect() as conn:
            conn.execute(test_sql)
        return True, "간단한 쿼리 실행까지 정상입니다."
    except ModuleNotFoundError as e:
        mod = str(e).split("'")[-2] if "'" in str(e) else str(e)
        suggestion = "oracledb" if "oracledb" in str(e) else "psycopg[binary]"
        return False, f"필요한 드라이버 모듈이 없습니다: {mod}\n→ pip install {suggestion}"
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"
    

def count_rows(src_engine: Engine, schema: str, table: str, where_text: str) -> int:
    where_sql = f" WHERE {where_text} " if where_text.strip() else ""
    sql = text(f"SELECT COUNT(*) AS cnt FROM {schema}.{table}{where_sql}")
    with src_engine.connect() as conn:
        r = conn.execute(sql).scalar()
        return int(r or 0)


def _get_columns(engine: Engine, schema: str, table: str) -> Iterable[str]:
    insp = inspect(engine)
    cols = [str(c["name"]).lower() for c in insp.get_columns(table, schema=schema)]
    if not cols:
        with engine.connect() as c:
            r = c.execute(text(f"SELECT * FROM {schema}.{table} FETCH FIRST 1 ROWS ONLY"))
            if r.returns_rows:
                cols = [str(k).lower() for k in r.keys()]
    return cols


def run_migration_stream(
    src_engine: Engine,
    dst_engine: Engine,
    *,
    src_schema: str,
    src_table: str,
    dst_schema: str,
    dst_table: str,
    where_text: str = "",
    chunk_size: int = 10_000,
) -> Generator[Dict, None, None]:
    cols = _get_columns(src_engine, src_schema, src_table)
    if not cols:
        yield {"type": "log", "message": f"[경고] 열 정보를 가져오지 못했습니다: {src_schema}.{src_table}"}
        return

    where_sql = f" WHERE {where_text} " if where_text.strip() else ""

    # DB별 SELECT 컬럼 표현(소스)
    src_dialect = (src_engine.dialect.name or "").lower()
    if src_dialect == "oracle":
        select_cols = ", ".join(f'{c.upper()} AS "{c}"' for c in cols)
    else:
        select_cols = ", ".join(f'"{c}" AS "{c}"' for c in cols)

    # INSERT(목적지): 기본은 따옴표 없이 소문자
    insert_cols = ", ".join(cols)
    binds = ", ".join(f":{c}" for c in cols)

    select_sql = text(f"SELECT {select_cols} FROM {src_schema}.{src_table}{where_sql}")
    insert_sql = text(f"INSERT INTO {dst_schema}.{dst_table} ({insert_cols}) VALUES ({binds})")

    inserted = 0
    row_index = 0

    with src_engine.connect() as src_conn, dst_engine.begin() as dst_tx:
        result = src_conn.execution_options(stream_results=True).execute(select_sql)
        while True:
            rows = result.fetchmany(chunk_size)
            if not rows:
                break
            payload = []
            for r in rows:
                row_index += 1
                try:
                    m = r._mapping
                    payload.append({c: m.get(c) for c in cols})
                except Exception as e:
                    yield {"type": "error", "row_index": row_index, "error": str(e)}
                    continue

            if not payload:
                continue

            try:
                dst_tx.execute(insert_sql, payload)
                inserted += len(payload)
                yield {"type": "progress", "inserted_delta": len(payload)}
                yield {"type": "log", "message": f"[청크] {len(payload)}건 삽입 성공 → {dst_schema}.{dst_table}"}
            except Exception as e:
                yield {"type": "log", "message": f"[주의] 청크 삽입 실패 → 개별행 재시도: {e}"}
                for idx, row in enumerate(payload, 1):
                    try:
                        dst_tx.execute(insert_sql, [row])
                        inserted += 1
                        yield {"type": "progress", "inserted_delta": 1}
                    except Exception as e2:
                        yield {"type": "error", "row_index": row_index - len(payload) + idx, "error": str(e2)}

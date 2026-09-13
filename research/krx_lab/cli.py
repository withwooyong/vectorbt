"""프로그램 진입점. 실제 주문 기능은 포함하지 않는다."""

import argparse
from pathlib import Path

from .config import default_config
from .io import write_json


def main(argv=None):
    parser = argparse.ArgumentParser(description="국내 주식 48개 전략 공동계좌 연구 도구")
    commands = parser.add_subparsers(dest="command", required=True)
    snapshot = commands.add_parser("snapshot", help="home PostgreSQL 읽기 전용 고정 추출")
    snapshot.add_argument("--out", required=True)
    snapshot.add_argument("--start", default="2015-01-02")
    snapshot.add_argument("--end", default="2023-12-31")
    synthetic = commands.add_parser("synthetic", help="시장 성과가 아닌 엔진 검증 자료 생성")
    synthetic.add_argument("--out", required=True)
    diagnostic = commands.add_parser("diagnose", help="매매 수익률 없이 실제 자료의 신호 빈도 검사")
    diagnostic.add_argument("--snapshot", required=True)
    diagnostic.add_argument("--out", required=True)
    config = commands.add_parser("config", help="실행용 사전 고정 설정 작성")
    config.add_argument("--snapshot", required=True)
    config.add_argument("--out", required=True)
    plan_parser = commands.add_parser("plan")
    plan_parser.add_argument("--config", required=True)
    plan_parser.add_argument("--out", required=True)
    for name in ("run", "resume", "status", "report", "select", "freeze", "finalize"):
        command = commands.add_parser(name)
        command.add_argument("--experiment", required=True, help="experiment.json이 있는 디렉터리")
        if name in ("run", "resume"):
            command.add_argument("--phase", default="development,validation")
            command.add_argument("--limit", type=int, help="운영 smoke용 실행 건수; 나머지는 PLANNED로 보존")
    args = parser.parse_args(argv)
    from . import runner
    from .snapshot import extract, synthetic_snapshot
    if args.command == "snapshot":
        result = extract(args.out, args.start, args.end)
        result = {k: result[k] for k in ("status", "rows", "created_at")}
    elif args.command == "synthetic":
        result = synthetic_snapshot(args.out)
        result = {"source": result["source"], "rows": result["rows"]}
    elif args.command == "diagnose":
        from .diagnostics import diagnose
        result = diagnose(args.snapshot, args.out)
    elif args.command == "config":
        if Path(args.out).exists():
            parser.error("기존 설정을 덮어쓸 수 없습니다")
        write_json(args.out, default_config(args.snapshot))
        result = {"config": str(Path(args.out).resolve())}
    elif args.command == "plan":
        result = runner.plan(args.config, args.out)
        result = {k: result[k] for k in ("experiment_id", "logical_slots", "quality")}
    elif args.command in ("run", "resume"):
        if args.limit is not None and args.limit < 1:
            parser.error("limit은 1 이상이어야 합니다")
        result = runner.run(args.experiment, args.phase.split(","), args.limit)
    elif args.command == "status":
        result = runner.status(args.experiment)
    elif args.command in ("report", "select"):
        runner.verify_experiment(args.experiment)
        result = runner.update_report(args.experiment)
        result = {k: result[k] for k in ("status", "selected_strategy_id", "candidate_count", "eligible_count")}
    else:
        parser.error("정식 데이터·현실 비용·기업행사 인수가 미완료여서 잠금/최종 선정을 활성화하지 않았습니다")
    import json
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()

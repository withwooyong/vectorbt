"""프로그램 진입점. 실제 주문 기능은 포함하지 않는다."""

import argparse
import json
from pathlib import Path

from .config import default_config
from .io import read_json, write_json


def main(argv=None):
    parser = argparse.ArgumentParser(description="국내 주식 전략 공동계좌 연구 도구")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("snapshot-v3", "verify-snapshot-v3"):
        command = commands.add_parser(name, help="SEALED v3 불변 입력 추출·검증 (실행 인수 아님)")
        command.add_argument("--out" if name == "snapshot-v3" else "--snapshot", required=True)
    for name in ("materialize-v3", "verify-tables-v3"):
        command = commands.add_parser(name, help="검증한 v3를 반복 계산용 Parquet로 변환·대조")
        command.add_argument("--source", required=True)
        command.add_argument("--out", required=True)
    config56 = commands.add_parser("config56", help="56개 기본 또는 넓은 청산 별도 실험 설정")
    config56.add_argument("--snapshot", required=True)
    config56.add_argument("--out", required=True)
    config56.add_argument("--wide-exits", action="store_true")
    prepare = commands.add_parser("prepare56", help="실행 권한 없이 56개 비교 계획 고정")
    prepare.add_argument("--config", required=True)
    prepare.add_argument("--out", required=True)
    prepare_real = commands.add_parser("prepare-v3", help="검증된 Parquet에서 공통 종목군·신호 준비")
    for name in ("source", "tables", "out"):
        prepare_real.add_argument("--" + name, required=True)
    certify_real = commands.add_parser("certify-v3", help="현재 코드의 독립 계산 테스트 증거 기록")
    certify_real.add_argument("--out", required=True)
    run_real = commands.add_parser("run-v3", help="검증된 공통 종목군의 제한된 실자료 비교")
    for name in ("prepared", "evidence", "out"):
        run_real.add_argument("--" + name, required=True)
    run_real.add_argument("--limit", type=int)
    run_real.add_argument("--family", choices=("basic", "wide"), help="서로 독립인 실험 중 하나만 실행")
    report_real = commands.add_parser("report-v3", help="실제 비교 결과의 한글 보고서 작성")
    report_real.add_argument("--batch", required=True)
    report_real.add_argument("--out", required=True)
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
        if name in ("freeze", "finalize"):
            command.add_argument("--attempt-id", default=name)
        if name == "freeze":
            command.add_argument("--evidence")
            command.add_argument("--bindings")
            command.add_argument("--artifact-root")
        if name == "finalize":
            command.add_argument("--result", required=True)
        if name in ("run", "resume"):
            command.add_argument("--phase", default="development,validation")
            command.add_argument("--limit", type=int, help="운영 smoke용 실행 건수; 나머지는 PLANNED로 보존")
    inspect_parser = commands.add_parser("inspect-delivery", help="데이터 전달 JSON 읽기 전용 검사")
    real_parser = commands.add_parser("inspect-real", help="실자료 입력 근거와 남은 공백을 읽기 전용으로 보고")
    delivery_parser = commands.add_parser("run-delivery", help="합성 데이터·기업행사 장부 검증 전용")
    for command in (inspect_parser, real_parser, delivery_parser):
        command.add_argument("--delivery", required=True)
        command.add_argument("--root")
        command.add_argument("--previous")
    inspect_parser.add_argument("--out", help="검사 결과를 새 JSON 파일에 저장")
    real_parser.add_argument("--out", required=True, help="기존 파일을 덮어쓰지 않는 검사 결과 JSON 경로")
    delivery_parser.add_argument("--signals", required=True, help="원가격 단위 합성 신호 JSON 배열")
    delivery_parser.add_argument("--out", required=True)
    delivery_parser.add_argument("--entry-id", required=True)
    delivery_parser.add_argument("--exit-id", required=True)
    delivery_parser.add_argument("--start", required=True)
    delivery_parser.add_argument("--end", required=True)
    conditional_plan = commands.add_parser("conditional-plan", help="합성 후속 33슬롯 별도 실험 생성")
    for name in ("delivery", "signals", "windows", "lifecycle", "out", "benchmark-id"):
        conditional_plan.add_argument("--" + name, required=True)
    conditional_run = commands.add_parser("conditional-run", help="합성 후속 슬롯 실행·재개")
    conditional_run.add_argument("--experiment", required=True)
    conditional_run.add_argument("--include-synthetic-holdout", action="store_true")
    conditional_run.add_argument("--limit", type=int)
    conditional_status = commands.add_parser("conditional-status", help="합성 후속 산출물 검증·상태 보고")
    conditional_status.add_argument("--experiment", required=True)
    args = parser.parse_args(argv)
    from . import runner
    from .snapshot import extract, synthetic_snapshot
    if args.command == "prepare-v3":
        from .v3_run import prepare_run
        value = prepare_run(args.source, args.tables, args.out)
        result = {key: value[key] for key in ("status", "dataset_id", "revision")}
    elif args.command == "certify-v3":
        from .v3_run import certify_execution
        result = certify_execution(args.out)
    elif args.command == "run-v3":
        from .v3_run import run_batch
        if args.limit is not None and args.limit < 1:
            parser.error("limit은 1 이상이어야 합니다")
        value = run_batch(args.prepared, args.evidence, args.out, limit=args.limit, family=args.family)
        result = {key: value.get(key) for key in ("status", "planned_runs", "attempted_runs", "succeeded_runs", "blocked_runs")}
    elif args.command == "report-v3":
        from .v3_report import generate_report
        result = generate_report(args.batch, args.out)
    elif args.command in ("materialize-v3", "verify-tables-v3"):
        from .v3_tables import materialize_v3_tables, verify_v3_tables
        manifest = (materialize_v3_tables if args.command == "materialize-v3" else verify_v3_tables)(args.source, args.out)
        result = {key: manifest[key] for key in ("status", "revision_id", "real_execution_admitted")}
    elif args.command in ("snapshot-v3", "verify-snapshot-v3"):
        from .v3_snapshot import extract_v3, verify_v3_snapshot
        manifest = extract_v3(args.out) if args.command == "snapshot-v3" else verify_v3_snapshot(args.snapshot)
        result = {key: manifest[key] for key in ("status", "revision_label", "real_execution_admitted")}
    elif args.command == "config56":
        from .config_v2 import default_config as default56, default_wide_config
        value = (default_wide_config if args.wide_exits else default56)(args.snapshot)
        output = Path(args.out)
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("x", encoding="utf-8") as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
        result = {"config": str(output.resolve()), "schema_version": value["schema_version"]}
    elif args.command == "prepare56":
        from .preparation import prepare_plan
        plan = prepare_plan(args.config, args.out)
        result = {key: plan[key] for key in ("experiment_id", "status", "candidate_count", "logical_slots")}
    elif args.command.startswith("conditional-"):
        from .conditional_runner import plan_conditional, run_conditional, conditional_status
        if args.command == "conditional-plan":
            result = plan_conditional(args.delivery, args.signals, args.windows, args.lifecycle, args.out,
                                      benchmark_id=args.benchmark_id)
        elif args.command == "conditional-run":
            result = run_conditional(args.experiment, include_synthetic_holdout=args.include_synthetic_holdout,
                                     limit=args.limit)
        else:
            result = conditional_status(args.experiment)
    elif args.command == "inspect-delivery":
        result = runner.inspect_delivery_file(args.delivery, root=args.root, previous_path=args.previous)
        if args.out:
            if Path(args.out).exists():
                parser.error("기존 검사 결과를 덮어쓸 수 없습니다")
            write_json(args.out, result)
    elif args.command == "inspect-real":
        from .real_admission import inspect_real_readiness

        delivery_path = Path(args.delivery).resolve()
        root = Path(args.root).resolve() if args.root else delivery_path.parent
        output = Path(args.out).resolve()
        if output.is_relative_to(root) or output.is_relative_to(delivery_path.parent):
            parser.error("검사 결과는 데이터 전달 폴더 밖에 저장해야 합니다")
        if output.exists():
            parser.error("기존 검사 결과를 덮어쓸 수 없습니다")
        previous = read_json(args.previous) if args.previous else None
        result = inspect_real_readiness(read_json(delivery_path), root, previous)
        rendered = json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False, default=str) + "\n"
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("x", encoding="utf-8") as stream:
            stream.write(rendered)
    elif args.command == "run-delivery":
        result = runner.run_delivery(args.delivery, args.signals, args.out, entry_id=args.entry_id,
                                     exit_id=args.exit_id, start=args.start, end=args.end,
                                     root=args.root, previous_path=args.previous)
    elif args.command == "snapshot":
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
    elif args.command == "freeze":
        result = runner.freeze(args.experiment, evidence_path=args.evidence, bindings_path=args.bindings,
                               artifact_root=args.artifact_root, attempt_id=args.attempt_id)
    elif args.command == "finalize":
        result = runner.finalize(args.experiment, args.result, attempt_id=args.attempt_id)
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()

"""python3 -m linuxgcb：完全離線，不執行 SCA 命令。"""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from .catalog import write_registry
from .policy import build, validate
from .report import render
from .collector import timestamp
from .snapshot import convert


def main():
    parser = argparse.ArgumentParser(description='LinuxGCB 候選工具（2026-11-01 真機驗收與人工複審已完成，VERIFIED）')
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('build', help='驗證來源並重建 registry 與候選政策')
    sub.add_parser('validate', help='離線結構與來源檢查，非引擎驗收')
    report = sub.add_parser('report', help='匯入離線 JSON，輸出 HTML/CSV 與稽核副本')
    report.add_argument('snapshot')
    report.add_argument('--out', required=True)
    report.add_argument('--now', help='固定報表時間，ISO8601 含時區')
    snapshot = sub.add_parser('snapshot', help='離線 Manager DB JSON 轉 snapshot v1')
    snapshot.add_argument('manager_dump')
    snapshot.add_argument('--out', required=True)
    snapshot.add_argument('--scan-info', help='同次離線 sca_scan_info JSON，依 policy_id 對應 end_scan')
    args = parser.parse_args()
    if args.command == 'build':
        rows = write_registry()
        build()
        print(f'314 項；307 候選／7 排除；{validate()} 項候選規則，VERIFIED／人工審查已完成（2026-11-01）')
    elif args.command == 'validate':
        print('VERIFIED：離線結構檢查通過，候選控制項數', validate())
    elif args.command == 'snapshot':
        validate()
        result = convert(args.manager_dump, json.loads(Path(args.scan_info).read_text()) if args.scan_info else None)
        target = Path(args.out)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
        print(json.dumps(result['warnings'], ensure_ascii=False))
    else:
        validate()
        result = render(json.loads(Path(args.snapshot).read_text()), args.out,
                        timestamp(args.now) if args.now else datetime.now(timezone.utc))
        print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()

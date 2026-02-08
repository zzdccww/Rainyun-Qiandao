"""模块入口：python -m rainyun（已废弃）。"""

import sys


def main() -> int:
    sys.stderr.write("CLI 已废弃，请使用 GitHub Actions 或 cron_runner 运行。\n")
    return 1


if __name__ == "__main__":
    sys.exit(main())

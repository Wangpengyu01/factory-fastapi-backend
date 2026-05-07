"""导出 FastAPI OpenAPI JSON。

后端接口变更后运行本脚本，把 app.main 中的接口定义同步到 backend/openapi.json。
"""

import json
from pathlib import Path
import sys

# ROOT 指向 backend 目录，插入 sys.path 后脚本可直接导入 app.main。
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.main import app


def main() -> None:
    """生成 OpenAPI 文件，供 Swagger、文档站和前端类型同步使用。"""
    output_file = ROOT / "openapi.json"
    output_file.write_text(
        json.dumps(app.openapi(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"OpenAPI written to: {output_file}")


if __name__ == "__main__":
    main()

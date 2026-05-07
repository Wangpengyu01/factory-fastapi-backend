from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import shutil

import jinja2
import markdown


ROOT = Path(__file__).resolve().parent
SITE_ROOT = ROOT / "blog-site"
DOCS_DIR = SITE_ROOT / "docs"
RAW_MD_DIR = SITE_ROOT / "md"


@dataclass(frozen=True)
class DocMeta:
    filename: str
    slug: str
    title: str
    summary: str
    audience: str
    section: str
    highlights: list[str]
    explanation: list[str]


DOCS: list[DocMeta] = [
    DocMeta(
        filename="API_SYNC_SUMMARY.md",
        slug="api-sync-summary",
        title="API 文档同步摘要",
        summary="记录本次 API 文档同步后的真实实现范围、方案文档范围和后续查看建议。",
        audience="需要快速判断哪些接口已经实现、哪些内容仍是方案稿的人。",
        section="同步摘要",
        highlights=[
            "当前仓库真实实现接口以 backend/app/main.py 和 backend/openapi.json 为准。",
            "大屏业务接口范围稿保留为方案文档，不等同于当前 FastAPI 已落地路由。",
            "README、API_DOC、设备状态控件文档和演示文档已按同一口径更新。",
        ],
        explanation=[
            "这篇是本次更新后的索引摘要，适合先看它来判断文档口径是否一致。",
            "如果要核对真实接口，应继续看 API_DOC 和线上 OpenAPI JSON；如果要讲业务方案，再看大屏范围稿。",
        ],
    ),
    DocMeta(
        filename="BLOG_NACOS_FASTAPI_BIGSCREEN.md",
        slug="bigscreen-api-scope",
        title="大屏业务接口范围稿",
        summary="用于汇报和划边界：明确哪些是当前仓库已实现接口，哪些只是业务侧方案文档。",
        audience="做汇报、联调边界确认、接口盘点时先看这一篇。",
        section="范围与边界",
        highlights=[
            "当前仓库已实现的只有 health、nacos-config 和 device-status 共 5 个接口。",
            "树菜单、测点、任务、首页概览属于业务侧接口范围稿，不是本仓库已落地路由。",
            "树节点 id 不是业务提交 ID，selected_points 的 ID 规则要单独讲清楚。",
        ],
        explanation=[
            "这篇文档的价值在于划清范围，避免开会时把“仓库里已经有实现”和“业务文档里有方案”混成一套。",
            "如果需要汇报螺栓、开距、预制点、任务这些业务接口，应该先看这篇再决定哪些内容属于当前项目范围。",
        ],
    ),
    DocMeta(
        filename="DASHBOARD_OVERVIEW_API_DOC.md",
        slug="dashboard-overview-api",
        title="首页概览接口方案稿",
        summary="聚焦首页概览聚合数据，说明 GET /api/dashboard/overview 为什么应该单独设计且尚未在本仓库落地。",
        audience="讨论首页卡片、筛选器、图表接口设计的人都该看。",
        section="建议新增接口",
        highlights=[
            "它承载 onlineAccess、areaTotal、vehiclesOnSite、railStatus 等首页聚合字段。",
            "deviceRecords、deviceRegions、deviceTypes 作为图表和筛选的公共数据源。",
            "截至 2026-04-22，它仍是方案稿，不在当前 FastAPI 路由和 OpenAPI 中。",
        ],
        explanation=[
            "这不是当前已实现接口，而是建议新增的首页聚合协议，所以单独成篇。",
            "如果后续首页统计维度继续扩展，也应该优先扩到这个接口里，而不是塞进当前的配置桥或设备状态接口。",
        ],
    ),
    DocMeta(
        filename="API_DOC.md",
        slug="api-doc",
        title="项目 API 总说明",
        summary="完整描述当前 FastAPI 项目已实现的 5 个接口、模型映射、错误码和前端调用示例。",
        audience="前后端都能用，尤其适合做联调和接口核对。",
        section="现有接口文档",
        highlights=[
            "覆盖 health、nacos 配置读写、device-status options/records。",
            "明确了 Base URL、错误码、TypeScript 类型和示例调用方式。",
            "单独说明了当前 FastAPI 返回裸 JSON，不使用 success/data 包装。",
        ],
        explanation=[
            "如果你要核对字段、参数或错误码，这篇是最接近接口契约的总文档。",
            "它适合作为开发过程中的查表文档，不适合作为会议里第一篇讲解文档。",
        ],
    ),
    DocMeta(
        filename="DEVICE_STATUS_WIDGET_8083_DOC.md",
        slug="device-status-widget-8083",
        title="8083 设备状态控件文档",
        summary="说明 8083 大屏控件当前的数据结构、筛选逻辑和已经落地的后端接口契约。",
        audience="接 8083 设备状态控件的前端和接口设计者。",
        section="控件专项文档",
        highlights=[
            "控件核心输入是 records、regions、devices。",
            "后端已拆成 options 和 records 两个接口，减少前端改动。",
            "records 支持 mock 数据和 Nacos 配置读取两种模式。",
            "当前 options 仍基于内置演示数据，和 records 的 dataId 模式存在边界。",
        ],
        explanation=[
            "这篇是专项控件文档，重点不是全站接口，而是让 8083 这个组件先无缝接上后端数据。",
            "如果你只改一个设备状态组件，优先看这篇，不用先通读所有接口文档。",
        ],
    ),
    DocMeta(
        filename="FRONTEND_DEMO_GUIDE.md",
        slug="frontend-demo-guide",
        title="前端演示文档",
        summary="给演示场景准备的话术和步骤，适合对外说明“现在能演示什么”。",
        audience="做现场演示、汇报或给前端过方案的人。",
        section="演示与汇报",
        highlights=[
            "按健康检查、Swagger、Nacos 配置、device-status options/records 的顺序讲。",
            "当前演示范围只有 5 个已实现接口，不包含树菜单、测点和任务接口。",
            "把 mock 联调边界讲清楚，能减少误解和返工。",
        ],
        explanation=[
            "这篇偏演示流程，不是纯接口规范，适合你开会或者录屏演示时照着走。",
            "如果你只想快速说明“东西已经跑通”，它比 API 总说明更适合作为发言底稿。",
        ],
    ),
    DocMeta(
        filename="README.md",
        slug="readme",
        title="项目 README",
        summary="项目入口说明，包含目录结构、启动方式、环境变量、访问地址和文档边界。",
        audience="刚接手项目或准备本地启动的人。",
        section="项目入口",
        highlights=[
            "先说明 backend、frontend 和各份文档分别是什么。",
            "给出 docker compose 启动方式、关键环境变量和已实现接口列表。",
            "明确区分当前仓库文档和业务方案文档的边界。",
        ],
        explanation=[
            "README 解决的是‘项目怎么跑起来’的问题，不是‘前端接口怎么接’的问题。",
            "第一次接手项目时先看 README，再跳到 API_DOC 或专项文档，会更省时间。",
        ],
    ),
]


BASE_TEMPLATE = """<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <meta name="description" content="{{ description }}" />
    <title>{{ title }} | Nacos FastAPI Blog</title>
    <link rel="stylesheet" href="/assets/styles.css" />
  </head>
  <body>
    <div class="page-shell">
      <header class="site-header">
        <a class="brand" href="/">
          <span class="brand-mark">NF</span>
          <span class="brand-text">
            <strong>Nacos FastAPI Blog</strong>
            <small>Bigscreen Integration Notes</small>
          </span>
        </a>
        <nav class="top-nav">
          <a href="/">首页</a>
          <a href="/docs/">文档总览</a>
          <a href="/posts/bigscreen-api-scope.html">范围说明</a>
        </nav>
      </header>
      {{ body | safe }}
      <footer class="site-footer">
        <p>当前页面由本地 Markdown 静态生成，原始文档可在站内直接查看或下载。</p>
      </footer>
    </div>
  </body>
</html>
"""


DOC_INDEX_BODY = """
<main>
  <section class="hero docs-hero">
    <div class="hero-copy">
      <p class="eyebrow">Markdown Docs</p>
      <h1>文档总览与讲解入口</h1>
      <p class="hero-text">
        这里集中放置原始 Markdown 文档、讲解页和阅读建议。适合先按角色选文档，再决定读原始协议还是看讲解版。
      </p>
    </div>
    <aside class="hero-panel">
      <div class="metric-card">
        <span class="metric-label">已发布文档</span>
        <strong>{{ docs|length }}</strong>
        <p>原始 Markdown 与讲解页同步提供</p>
      </div>
      <div class="metric-card">
        <span class="metric-label">推荐阅读顺序</span>
        <strong>3 步</strong>
        <p>先看范围，再看总说明，最后看专项文档</p>
      </div>
    </aside>
  </section>

  <section class="docs-grid">
    <article class="doc-card">
      <div class="doc-card-head">
        <span class="doc-tag">OpenAPI</span>
        <h2>当前 OpenAPI JSON</h2>
        <p>这里是后端当前导出的接口定义文件，适合用来核对真实已实现路由和字段结构。</p>
      </div>
      <p class="doc-audience">需要生成接口类型、导入 Swagger 工具或核对真实接口时优先看它。</p>
      <ul class="flat-list">
        <li>文件来源：<code>backend/openapi.json</code></li>
        <li>线上地址：<code>/openapi.json</code></li>
      </ul>
      <div class="doc-actions">
        <a class="button button-primary" href="/openapi.json">查看 JSON</a>
      </div>
    </article>
    {% for doc in docs %}
    <article class="doc-card">
      <div class="doc-card-head">
        <span class="doc-tag">{{ doc.section }}</span>
        <h2>{{ doc.title }}</h2>
        <p>{{ doc.summary }}</p>
      </div>
      <p class="doc-audience">{{ doc.audience }}</p>
      <ul class="flat-list">
        {% for item in doc.highlights %}
        <li>{{ item }}</li>
        {% endfor %}
      </ul>
      <div class="doc-actions">
        <a class="button button-primary" href="/docs/{{ doc.slug }}.html">看讲解页</a>
        <a class="button button-secondary" href="/md/{{ doc.filename }}">原始 MD</a>
      </div>
    </article>
    {% endfor %}
  </section>
</main>
"""


DOC_PAGE_BODY = """
<main class="article-layout">
  <aside class="article-sidebar">
    <div class="sticky-card toc-card">
      <p class="card-kicker">目录</p>
      <a href="/docs/">返回文档总览</a>
      <a href="/md/{{ doc.filename }}">原始 Markdown</a>
      {{ toc|safe }}
    </div>
  </aside>

  <article class="article-card">
    <p class="eyebrow">{{ doc.section }}</p>
    <h1>{{ doc.title }}</h1>
    <p class="lede">{{ doc.summary }}</p>

    <section class="article-section">
      <div class="article-meta-grid">
        <div class="note-card note-implemented">
          <p class="card-kicker">适合谁看</p>
          <p>{{ doc.audience }}</p>
        </div>
        <div class="note-card note-suggested">
          <p class="card-kicker">原始文档</p>
          <p><a class="text-link" href="/md/{{ doc.filename }}">{{ doc.filename }}</a></p>
        </div>
      </div>
    </section>

    <section class="article-section">
      <h2>怎么读这篇文档</h2>
      <ul class="flat-list">
        {% for item in doc.explanation %}
        <li>{{ item }}</li>
        {% endfor %}
      </ul>
    </section>

    <section class="article-section">
      <h2>关键点</h2>
      <ul class="flat-list">
        {% for item in doc.highlights %}
        <li>{{ item }}</li>
        {% endfor %}
      </ul>
    </section>

    <section class="article-section markdown-body">
      {{ content | safe }}
    </section>
  </article>
</main>
"""


def render_markdown(md_text: str) -> tuple[str, str]:
    parser = markdown.Markdown(
        extensions=["fenced_code", "tables", "sane_lists", "toc"],
        extension_configs={"toc": {"permalink": False}},
        output_format="html5",
    )
    html = parser.convert(md_text)
    toc = parser.toc or "<ul><li>本文档没有可提取的目录</li></ul>"
    return html, toc


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def main() -> None:
    env = jinja2.Environment(autoescape=True, trim_blocks=True, lstrip_blocks=True)
    base_template = env.from_string(BASE_TEMPLATE)
    doc_index_template = env.from_string(DOC_INDEX_BODY)
    doc_page_template = env.from_string(DOC_PAGE_BODY)

    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    RAW_MD_DIR.mkdir(parents=True, exist_ok=True)

    docs_payload: list[dict[str, object]] = []

    for doc in DOCS:
        source = ROOT / doc.filename
        if not source.exists():
            raise FileNotFoundError(f"missing source markdown: {source}")

        raw_target = RAW_MD_DIR / doc.filename
        shutil.copyfile(source, raw_target)

        md_text = source.read_text(encoding="utf-8")
        rendered_html, toc = render_markdown(md_text)

        body = doc_page_template.render(doc=doc, content=rendered_html, toc=toc)
        page = base_template.render(
            title=doc.title,
            description=doc.summary,
            body=body,
        )
        write_text(DOCS_DIR / f"{doc.slug}.html", page)
        docs_payload.append(doc.__dict__)

    index_body = doc_index_template.render(docs=docs_payload)
    index_page = base_template.render(
        title="文档总览",
        description="Nacos FastAPI Bigscreen 相关 Markdown 文档与讲解页总览。",
        body=index_body,
    )
    write_text(DOCS_DIR / "index.html", index_page)

    openapi_source = ROOT / "backend" / "openapi.json"
    if openapi_source.exists():
        shutil.copyfile(openapi_source, SITE_ROOT / "openapi.json")


if __name__ == "__main__":
    main()

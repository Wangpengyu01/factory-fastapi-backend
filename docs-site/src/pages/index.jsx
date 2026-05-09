import React from "react";
import Link from "@docusaurus/Link";
import Layout from "@theme/Layout";

// 文档站首页：给团队成员一个版本化入口，不承载具体 API 细节。
export default function Home() {
  return (
    <Layout
      title="Factory API Docs"
      description="DOC-2026.05.08：8083 Vue + Vite 前端保留，FastAPI 已补齐大屏聚合与 Nacos 模拟器链路。"
    >
      <header className="heroBanner">
        <div className="heroBanner__inner">
          <h1>Factory API Docs</h1>
          <p>
            当前文档集版本为 DOC-2026.05.08。8083 Vue + Vite 前端入口保留，后端已补齐大屏聚合接口和 Python 模拟器写 Nacos 链路，接口契约按 API-CURRENT-0.2 和 API-TARGET-1.0 区分。
          </p>
          <Link className="button button--primary button--lg" to="/docs/version-guide">
            查看版本说明
          </Link>
        </div>
      </header>

      <main className="quickGrid">
        {/* 快捷卡片只链接到关键文档，完整目录在左侧边栏。 */}
        <Link className="quickCard" to="/docs/version-guide">
          <h2>版本说明</h2>
          <p>区分 LEGACY-FE、API-CURRENT、API-TARGET、SIM、OPENAPI 和 DOC 版本。</p>
        </Link>
        <Link className="quickCard" to="/docs/frontend-full-landing-task-book">
          <h2>前端全量任务</h2>
          <p>Vue + Vite、8083 调试、路由、Pinia、API 封装、页面落地和验收清单。</p>
        </Link>
        <Link className="quickCard" to="/docs/backend-full-landing-task-book">
          <h2>后端全量任务</h2>
          <p>按 API-TARGET-1.0 补齐 71 个操作，统一返回结构、状态码和字段契约。</p>
        </Link>
        <Link className="quickCard" to="/docs/backend-current-api">
          <h2>当前已落地 API</h2>
          <p>API-CURRENT-0.2 已运行接口、请求响应、curl 示例和后续实现边界。</p>
        </Link>
        <Link className="quickCard" to="/docs/dashboard-aggregate-nacos-chain-api">
          <h2>大屏聚合接口</h2>
          <p>补齐中心区域、事件看板、风险预警，以及模拟器写 Nacos 的完整链路。</p>
        </Link>
        <Link className="quickCard" to="/docs/frontend-gap-api-completion">
          <h2>前端缺口 API</h2>
          <p>中间主画面、右侧三个面板、底部子系统入口和默认接口模式的补齐口径。</p>
        </Link>
        <Link className="quickCard" to="/docs/hardware-state-machine-simulator">
          <h2>硬件模拟器</h2>
          <p>SIM-0.1：用 Python 状态机模拟门禁、道闸、传感器和报警器状态。</p>
        </Link>
        <Link className="quickCard" to="/openapi">
          <h2>Scalar OpenAPI</h2>
          <p>OPENAPI-8082-CURRENT-2026.05.07 的交互式接口文档。</p>
        </Link>
      </main>
    </Layout>
  );
}

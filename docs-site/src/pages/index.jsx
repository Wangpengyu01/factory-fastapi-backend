import React from "react";
import Link from "@docusaurus/Link";
import Layout from "@theme/Layout";

export default function Home() {
  return (
    <Layout
      title="Factory API Docs"
      description="DOC-2026.05.07：8083 Vue + Vite 前端保留，FastAPI 后端从零到一落地。"
    >
      <header className="heroBanner">
        <div className="heroBanner__inner">
          <h1>Factory API Docs</h1>
          <p>
            当前文档集版本为 DOC-2026.05.07。8083 Vue + Vite 前端入口保留，后端按 FastAPI 从零到一落地，接口契约按 API-CURRENT-0.1 和 API-TARGET-1.0 区分。
          </p>
          <Link className="button button--primary button--lg" to="/docs/version-guide">
            查看版本说明
          </Link>
        </div>
      </header>

      <main className="quickGrid">
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
          <p>API-CURRENT-0.1 已运行接口、请求响应、curl 示例和后续实现边界。</p>
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

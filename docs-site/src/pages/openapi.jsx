import React from "react";
import BrowserOnly from "@docusaurus/BrowserOnly";
import Layout from "@theme/Layout";

// Scalar 只在浏览器端加载，避免 Docusaurus 服务端渲染时报 window 相关错误。
function ScalarReference() {
  const { ApiReferenceReact } = require("@scalar/api-reference-react");

  return (
    <ApiReferenceReact
      configuration={{
        // 当前 Scalar React 版本使用顶层 url 配置，不再使用旧版 spec.url。
        url: "/openapi.json",
        layout: "modern",
        theme: "default",
        defaultHttpClient: {
          targetKey: "javascript",
          clientKey: "fetch"
        }
      }}
    />
  );
}

export default function OpenApiPage() {
  return (
    <Layout title="Scalar OpenAPI" description="当前可用 API 的交互式 OpenAPI 文档。">
      <main className="scalarShell">
        {/* 保留 JSON 直链，Scalar 页面异常时也能直接打开 OpenAPI 文件排查。 */}
        <div className="openapiLinks">
          <a href="https://wpengu.top/openapi.json" target="_blank" rel="noreferrer">
            openapi.json
          </a>
          <a href="/openapi/openapi-8082-current.json" target="_blank" rel="noreferrer">
            openapi-8082-current.json
          </a>
        </div>
        <BrowserOnly fallback={<div style={{ padding: 24 }}>OpenAPI 文档加载中...</div>}>
          {() => <ScalarReference />}
        </BrowserOnly>
      </main>
    </Layout>
  );
}

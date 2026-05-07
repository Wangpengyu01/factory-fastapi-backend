import React from "react";
import BrowserOnly from "@docusaurus/BrowserOnly";
import Layout from "@theme/Layout";

function ScalarReference() {
  const { ApiReferenceReact } = require("@scalar/api-reference-react");

  return (
    <ApiReferenceReact
      configuration={{
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

// @ts-check

// Docusaurus 文档站配置：用于发布团队 API 文档和 Scalar OpenAPI 页面。
const config = {
  title: "Factory API Docs",
  tagline: "DOC-2026.05.07：8083 Vue + Vite 前端保留，FastAPI 后端从零到一落地",
  favicon: "img/favicon.ico",

  url: "https://wpengu.top",
  baseUrl: "/",

  organizationName: "wpengu",
  projectName: "factory-api-docs",

  onBrokenLinks: "warn",
  onBrokenMarkdownLinks: "warn",

  i18n: {
    defaultLocale: "zh-CN",
    locales: ["zh-CN"]
  },

  presets: [
    [
      "classic",
      {
        docs: {
          sidebarPath: "./sidebars.js",
          routeBasePath: "/docs"
        },
        blog: false,
        theme: {
          customCss: "./src/css/custom.css"
        }
      }
    ]
  ],

  themeConfig: {
    navbar: {
      title: "Factory API Docs",
      // 顶部导航只放团队最常用入口，详细目录放到 sidebars.js。
      items: [
        { to: "/docs/intro", label: "文档入口", position: "left" },
        { to: "/docs/version-guide", label: "版本说明", position: "left" },
        { to: "/openapi", label: "Scalar OpenAPI", position: "left" },
        { href: "https://wpengu.top/openapi.json", label: "OpenAPI JSON", position: "left" }
      ]
    },
    footer: {
      style: "dark",
      // 页脚用于快速回到文档入口和接口契约。
      links: [
        {
          title: "文档",
          items: [
            { label: "文档入口", to: "/docs/intro" },
            { label: "版本说明", to: "/docs/version-guide" },
            { label: "API 契约", to: "/docs/team-api-contract" },
            { label: "Scalar OpenAPI", to: "/openapi" }
          ]
        }
      ],
      copyright: `Copyright © ${new Date().getFullYear()} Factory API Docs`
    },
    colorMode: {
      defaultMode: "light",
      disableSwitch: false,
      respectPrefersColorScheme: true
    }
  }
};

module.exports = config;

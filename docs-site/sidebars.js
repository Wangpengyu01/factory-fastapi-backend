// 左侧文档目录按团队使用场景分组，避免所有文档堆在一个分类下。
const sidebars = {
  tutorialSidebar: [
    {
      type: "category",
      label: "版本与入口",
      items: ["intro", "version-guide"]
    },
    {
      type: "category",
      label: "落地任务书",
      items: [
        "fastapi-8082-rebuild-task-book",
        "backend-full-landing-task-book",
        "frontend-full-landing-task-book"
      ]
    },
    {
      type: "category",
      label: "当前已落地",
      items: [
        "backend-current-api",
        "api-compliance-gap-101-8082",
        "dashboard-aggregate-nacos-chain-api",
        "frontend-gap-api-completion",
        "hardware-state-machine-simulator"
      ]
    },
    {
      type: "category",
      label: "接口契约",
      items: [
        "team-api-contract",
        "protocol-api-gap-and-supplement",
        "complete-api-doc"
      ]
    },
    {
      type: "category",
      label: "从零搭建",
      items: ["developer-rebuild"]
    }
  ]
};

module.exports = sidebars;

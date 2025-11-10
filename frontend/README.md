# AI 工具热点 Dashboard - React 前端

这是一个现代化的 React + Tailwind CSS 前端应用，用于展示 AI 工具、热点话题和机会洞察。

## 技术栈

- **框架**: React 18 + Vite
- **样式**: Tailwind CSS（深色主题 + 玻璃态效果）
- **路由**: React Router v6
- **图标**: Lucide React
- **数据可视化**: Recharts（待集成）
- **动画**: React-Bits（待集成）

## 功能特性

### ✨ 核心功能

- **首页 Dashboard**: 展示统计概览、最新工具和话题
- **AI 工具榜**: 浏览所有 AI 工具，支持搜索和按来源筛选
- **热点榜**: 查看热门话题，按热度排序
- **机会榜**: 查看 AI 领域机会，支持折叠展开查看详情

### 🎨 UI 特性

- 深色主题 + 紫蓝渐变科技风格
- 玻璃态卡片（毛玻璃效果）
- 悬浮动画和过渡效果
- 响应式设计（桌面/平板/手机）
- 自定义滚动条

### ⚡ 性能优化

- 数据缓存（5分钟 localStorage 缓存）
- 分页加载（减少渲染压力）
- 懒加载组件（代码分割）

## 开发指南

### 安装依赖

```bash
cd frontend
npm install
```

### 启动开发服务器

```bash
npm run dev
```

访问 http://localhost:5173

### 构建生产版本

```bash
npm run build
```

构建输出在 `dist/` 目录。

### 预览生产版本

```bash
npm run preview
```

## 项目结构

```
frontend/
├── public/
│   └── data/
│       └── latest.json          # 数据文件（从父目录 data/ 复制）
├── src/
│   ├── components/              # 可复用组件
│   │   ├── Layout.jsx          # 布局组件
│   │   └── Navbar.jsx          # 导航栏
│   ├── pages/                   # 页面组件
│   │   ├── Home.jsx            # 首页
│   │   ├── Tools.jsx           # 工具榜
│   │   ├── Trends.jsx          # 热点榜
│   │   └── Opportunities.jsx   # 机会榜
│   ├── services/               # 服务层
│   │   └── dataService.js      # 数据加载服务
│   ├── lib/                    # 工具函数
│   │   └── utils.js            # 通用工具函数
│   ├── App.jsx                 # 应用主组件（路由配置）
│   ├── main.jsx                # 入口文件
│   └── index.css               # 全局样式
├── tailwind.config.js          # Tailwind CSS 配置
├── postcss.config.js           # PostCSS 配置
└── vite.config.js              # Vite 配置
```

## 数据更新

数据文件位于 `public/data/latest.json`。每次 GitHub Actions 运行后，需要手动或自动复制最新数据：

```bash
# 从项目根目录执行
cp data/latest.json frontend/public/data/latest.json
```

## 后续改进

### 阶段 4: 集成 React-Bits 动画

- [ ] 安装 React-Bits CLI
- [ ] 添加页面加载动画
- [ ] 添加数据更新动画
- [ ] 添加交互式背景效果

### 阶段 5: 部署配置

- [ ] 配置 Vercel 部署
- [ ] 配置 GitHub Actions 自动部署
- [ ] 优化构建产物
- [ ] 添加 SEO 元数据

## 部署选项

### 1. Vercel（推荐）

1. 在 Vercel 导入项目
2. 设置根目录为 `frontend`
3. 构建命令: `npm run build`
4. 输出目录: `dist`
5. 自动部署

### 2. GitHub Pages

```bash
# 构建
npm run build

# 部署到 gh-pages 分支
npm install -g gh-pages
gh-pages -d dist
```

### 3. Netlify

拖拽 `dist` 目录到 Netlify 即可。

## 常见问题

### 数据加载失败？

检查 `public/data/latest.json` 文件是否存在且格式正确。

### 样式不生效？

确保 Tailwind CSS 正确配置，运行 `npm run dev` 重新启动。

### 构建失败？

清除缓存并重新安装依赖：

```bash
rm -rf node_modules dist
npm install
npm run build
```

## 许可证

MIT License

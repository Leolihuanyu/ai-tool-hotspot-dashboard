# Vercel 部署指南

> 本指南详细说明如何将前端部署到 Vercel，实现零冷启动和快速加载。

---

## 📋 部署前准备

### 1. 前端代码已更新
- ✅ dataService.js 已配置从 GitHub Raw 读取数据
- ✅ 环境变量配置文件已创建（.env.example、.env.production.example）
- ✅ .gitignore 已更新，保护 .env 文件
- ✅ 前端构建测试通过

### 2. 需要的信息
- GitHub 仓库地址
- Render.com 后端 API URL（用于认证、支付等）

---

## 🚀 Vercel 部署步骤

### 方式1：通过 Vercel Web 界面部署（推荐）

#### Step 1: 连接 GitHub 仓库

1. 访问 [Vercel Dashboard](https://vercel.com/dashboard)
2. 点击 "Add New" → "Project"
3. 选择 "Import Git Repository"
4. 授权 Vercel 访问 GitHub
5. 选择仓库：`ai-tool-hotspot-dashboard`
6. 点击 "Import"

#### Step 2: 配置项目设置

**Framework Preset**: Vite
**Root Directory**: `frontend`（重要！）
**Build Command**: `npm run build`
**Output Directory**: `dist`
**Install Command**: `npm install`

#### Step 3: 配置环境变量

在 "Environment Variables" 部分添加以下变量：

| 变量名 | 值 | 环境 |
|--------|----|----|
| `VITE_DATA_URL` | `https://raw.githubusercontent.com/Leolihuanyu/ai-tool-hotspot-dashboard/main/data/latest.json` | Production, Preview |
| `VITE_API_BASE_URL` | `https://your-app-name.onrender.com` | Production, Preview |
| `VITE_DEBUG` | `false` | Production |

**重要提示**：
- 请将 `your-app-name` 替换为你的实际 Render.com 应用名称
- 环境变量必须以 `VITE_` 开头才能在前端访问

#### Step 4: 部署

1. 点击 "Deploy" 按钮
2. 等待构建完成（通常需要 1-2 分钟）
3. 部署成功后，Vercel 会提供一个 URL（如 `https://your-project.vercel.app`）

---

### 方式2：通过 Vercel CLI 部署

#### Step 1: 安装 Vercel CLI

```bash
npm install -g vercel
```

#### Step 2: 登录 Vercel

```bash
vercel login
```

#### Step 3: 进入前端目录并部署

```bash
cd frontend
vercel
```

按照提示操作：
- Setup and deploy? **Y**
- Which scope? 选择你的账号
- Link to existing project? **N**
- What's your project's name? `ai-tool-hotspot-dashboard-frontend`
- In which directory is your code located? `./`
- Want to override the settings? **Y**
  - Build Command: `npm run build`
  - Output Directory: `dist`
  - Development Command: `npm run dev`

#### Step 4: 设置环境变量

```bash
# 生产环境
vercel env add VITE_DATA_URL production
# 输入值：https://raw.githubusercontent.com/Leolihuanyu/ai-tool-hotspot-dashboard/main/data/latest.json

vercel env add VITE_API_BASE_URL production
# 输入值：https://your-app-name.onrender.com

vercel env add VITE_DEBUG production
# 输入值：false
```

#### Step 5: 重新部署（应用环境变量）

```bash
vercel --prod
```

---

## ⚙️ 配置自定义域名（可选）

### Step 1: 在 Vercel 添加域名

1. 进入项目设置 → Domains
2. 添加你的域名（如 `dashboard.yourdomain.com`）
3. Vercel 会提供 DNS 配置信息

### Step 2: 配置 DNS

在你的域名提供商（如 Cloudflare、Namecheap）添加 DNS 记录：

**CNAME 记录**：
```
Name: dashboard (或其他子域名)
Value: cname.vercel-dns.com
```

或者 **A 记录**：
```
Name: @ (或子域名)
Value: 76.76.21.21
```

### Step 3: 等待 DNS 生效

通常需要 5-30 分钟，最长可能需要 48 小时。

---

## 🔧 vercel.json 配置（可选高级配置）

创建 `frontend/vercel.json` 文件：

```json
{
  "buildCommand": "npm run build",
  "outputDirectory": "dist",
  "framework": "vite",
  "rewrites": [
    {
      "source": "/api/:path*",
      "destination": "https://your-app-name.onrender.com/api/:path*"
    }
  ],
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        {
          "key": "X-Content-Type-Options",
          "value": "nosniff"
        },
        {
          "key": "X-Frame-Options",
          "value": "DENY"
        },
        {
          "key": "X-XSS-Protection",
          "value": "1; mode=block"
        }
      ]
    }
  ]
}
```

**说明**：
- `rewrites`: 将 `/api/*` 请求代理到 Render 后端（替代 Vite 开发服务器的代理）
- `headers`: 添加安全头部

---

## 📊 部署后验证

### 1. 检查部署状态

访问 Vercel 提供的 URL，确认：
- ✅ 页面正常加载
- ✅ 数据从 GitHub Raw 正确加载
- ✅ 搜索、过滤、分页功能正常
- ✅ 移动端响应式正常

### 2. 测试 API 调用

尝试需要后端 API 的功能：
- 邀请码注册
- Token 验证
- Stripe 支付（如果已配置）

### 3. 性能测试

使用 [PageSpeed Insights](https://pagespeed.web.dev/) 或 Lighthouse 测试性能：
- Performance 目标：>90
- Accessibility 目标：>90
- Best Practices 目标：>90
- SEO 目标：>80

---

## 🐛 常见问题排查

### 问题1：环境变量未生效

**症状**：前端无法加载数据，控制台显示 `undefined`

**解决方案**：
1. 确认环境变量名以 `VITE_` 开头
2. 在 Vercel Dashboard 检查环境变量是否正确设置
3. 重新部署项目（环境变量更改后需要重新部署）

```bash
vercel --prod --force
```

### 问题2：API 请求 CORS 错误

**症状**：浏览器控制台显示 CORS 错误

**解决方案**：
1. 确认 Render 后端已添加 CORS 配置（见下一步）
2. 确认 `VITE_API_BASE_URL` 配置正确
3. 检查 Flask 后端 CORS 允许的域名

### 问题3：构建失败

**症状**：Vercel 构建时报错

**解决方案**：
1. 检查 `frontend/package.json` 中的依赖是否完整
2. 确认 Root Directory 设置为 `frontend`
3. 查看构建日志，定位具体错误
4. 本地测试构建：`npm run build`

### 问题4：页面 404

**症状**：刷新页面时出现 404

**解决方案**：
添加 `vercel.json` 重写规则：

```json
{
  "rewrites": [
    {
      "source": "/(.*)",
      "destination": "/index.html"
    }
  ]
}
```

---

## 🔄 持续部署（CI/CD）

Vercel 默认启用自动部署：
- **主分支** push → 自动部署到生产环境
- **其他分支** push → 自动部署到预览环境

### 配置部署分支

在 Vercel Dashboard → Settings → Git：
- Production Branch: `main`
- 可以忽略特定分支或路径的部署

---

## 📈 监控与分析

### Vercel Analytics

Vercel 提供免费的分析功能（需要安装 SDK）：

```bash
cd frontend
npm install @vercel/analytics
```

在 `frontend/src/main.jsx` 中添加：

```javascript
import { inject } from '@vercel/analytics';

inject();
```

### 自定义监控

推荐集成：
- **Google Analytics 4**：网站流量分析
- **Sentry**：错误监控
- **LogRocket**：用户会话回放

---

## ✅ 部署检查清单

在部署到生产环境之前，确认：

- [ ] 前端代码已提交到 Git
- [ ] 环境变量已在 Vercel 配置
- [ ] `.env` 文件已添加到 `.gitignore`
- [ ] 本地构建测试通过（`npm run build`）
- [ ] Render 后端已部署并可访问
- [ ] CORS 配置已添加到 Flask 后端
- [ ] 所有功能本地测试通过

---

## 📚 相关文档

- [Vercel 官方文档](https://vercel.com/docs)
- [Vite 部署指南](https://vitejs.dev/guide/static-deploy.html)
- [CORS 配置指南](./FLASK_CORS_SETUP.md)（待创建）
- [Phase 6 详细计划](./PHASE6_DETAILED_PLAN.md)

---

**下一步**: 精简 Flask 后端，移除 HTML 路由并添加 CORS 配置

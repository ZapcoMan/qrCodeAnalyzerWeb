# 二维码解析器 Web 项目


<div align="center">

![https://img.shields.io/badge/Python-3.10+-blue](https://img.shields.io/badge/Python-3.10%2B-blue)
![https://img.shields.io/badge/Flask-3.0.0-brightgreen](https://img.shields.io/badge/Flask-3.0.0-brightgreen)
![https://img.shields.io/badge/Vue-3.x-green](https://img.shields.io/badge/Vue-3.x-green)
![https://img.shields.io/badge/TypeScript-5.x-blue](https://img.shields.io/badge/TypeScript-5.x-blue)
![https://img.shields.io/badge/Vite-6.x-orange](https://img.shields.io/badge/Vite-6.x-orange)
![https://img.shields.io/badge/License-MIT-yellow](https://img.shields.io/badge/License-MIT-yellow)

**基于 Flask + Vue 3 的现代化二维码解析器**

[快速开始](#-快速开始) • [项目结构](#-项目结构) • [API 文档](#-api-文档) • [技术特性](#-技术特性)

</div>


---

## 📋 项目简介

二维码解析器是一个功能完善的全栈应用，支持上传图片或通过 URL 解析二维码内容，采用多种图像预处理技术提高识别率。

### ✨ 核心特性

- 🏗️ **前后端分离架构**：Flask 3.0 + Vue 3 + Vite 6
- 📤 **多方式输入**：支持上传本地图片或通过 URL 解析
- 🚀 **智能图像预处理**：灰度化、二值化、对比度增强、高斯模糊等
- 🔍 **多编码支持**：UTF-8、GBK、GB2312 编码自动识别
- 🌈 **现代化 UI**：渐变背景、毛玻璃效果、流畅动画
- 📱 **响应式设计**：支持 PC 和移动端访问
- 🔒 **CORS 跨域支持**：已配置全局跨域
- 🧹 **自动资源清理**：临时文件自动删除

### 🛠️ 技术栈

| 分类 | 技术 |
|------|------|
| **后端** | Flask 3.0.0, Flask-CORS, pyzxing 1.1.1, Pillow 12.2.0 |
| **前端** | Vue 3, TypeScript, Vite 6, Axios |
| **图像处理** | PIL (Pillow), NumPy |
| **部署** | Python Virtual Environment |

---

## 🚀 快速开始

### ⚡ 方式一：快速启动（推荐）

**1. 启动后端服务**

打开终端 1：
```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python main.py
```

✅ 后端地址：http://localhost:5000  
✅ 健康检查：http://localhost:5000/

**2. 启动前端服务**

打开终端 2：
```powershell
cd frontend
npm run dev
```

✅ 前端地址：http://localhost:5173

---

### 💻 方式二：开发模式（首次配置）

#### 前置要求

- Python 3.10+
- Node.js 18+
- npm 或 yarn

#### 1. 后端配置

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py
```

#### 2. 前端配置

```powershell
cd frontend
npm install
npm run dev
```

---

## 📁 项目结构

```
qrCodeAnalyzerWeb/
├── 📄 README.md                    # 项目说明（本文件）
├── 📄 .gitignore                   # Git 忽略配置
├── 📂 backend/                      # 后端项目
│   ├── 📄 main.py                   # 主应用入口
│   ├── 📄 requirements.txt          # Python 依赖
│   └── 📂 .venv/                    # Python 虚拟环境（已忽略）
│       ├── Scripts/                 # 脚本文件
│       └── Lib/                     # 库文件
└── 📂 frontend/                     # 前端项目
    ├── 📄 package.json              # Node 依赖配置
    ├── 📄 vite.config.ts            # Vite 配置（含代理）
    ├── 📄 tsconfig.json             # TypeScript 配置
    ├── 📂 public/                   # 静态资源
    └── 📂 src/                      # 源代码
        ├── 📄 main.ts               # 入口文件
        ├── 📄 App.vue               # 根组件
        ├── 📄 style.css             #       全局样式
        └── 📂 components/           # 组件目录
            └── QRCodeDecoder.vue    # 二维码解析组件
```

---

## 📖 API 文档

### 主要接口

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| 🏠 首页 | GET | `/` | API 接口说明 |
| 📤 上传解析 | POST | `/decode` | 上传图片解析二维码 |
| 🔗 URL 解析 | POST | `/decode_url` | 通过 URL 解析二维码 |

### 接口详细说明

#### 1. 上传图片解析

**请求：**
```bash
POST /decode
Content-Type: multipart/form-data

# 参数
file: <图片文件>
```

**响应（成功）：**
```json
{
  "success": true,
  "result": "二维码内容",
  "type": "QRCODE"
}
```

**响应（失败）：**
```json
{
  "success": false,
  "error": "无法解析二维码，请确保图片清晰且包含有效的二维码"
}
```

#### 2. 通过 URL 解析

**请求：**
```bash
POST /decode_url
Content-Type: application/json

{
  "url": "https://example.com/qrcode.png"
}
```

**响应（成功）：**
```json
{
  "success": true,
  "result": "二维码内容",
  "type": "QRCODE"
}
```

---

## 🎨 前端架构

### 组件结构

```
frontend/src/
├── components/
│   └── QRCodeDecoder.vue    # 核心解析组件
│       ├── 上传区域（拖拽支持）
│       ├── 文件预览
│       ├── 解析按钮
│       └── 结果展示
├── App.vue                  # 根组件
├── main.ts                  # 入口文件
└── style.css                # 全局样式
```

### 核心功能

1. **文件上传**：支持点击选择和拖拽上传
2. **实时预览**：显示文件名和大小，支持删除
3. **智能解析**：自动调用后端 API
4. **动画效果**：加载动画、结果淡入动画
5. **错误处理**：友好的错误提示

---

## 🧠 图像处理技术

项目采用多种图像预处理技术提高二维码识别率：

| 技术 | 说明 |
|------|------|
| 灰度化 | 转换为单通道灰度图像 |
| 对比度增强 | 提高图像对比度 |
| 二值化 | 多种阈值（64、128、192） |
| 高斯模糊 | 去噪处理 |
| 图像锐化 | 增强细节 |
| 颜色反转 | 针对反色二维码 |
| 尺寸放大 | 针对小尺寸二维码 |
| 区域裁剪 | 四角区域分别识别 |

---

## 🔧 配置说明

### 后端配置

后端服务默认配置：
- **端口**：5000
- **主机**：0.0.0.0（支持外部访问）
- **调试模式**：开启

### 前端配置

前端代理配置（`vite.config.ts`）：
```typescript
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:5000',
      changeOrigin: true,
      rewrite: (path) => path.replace(/^\/api/, '')
    }
  }
}
```

---

## 📝 使用说明

1. **打开前端页面**：访问 http://localhost:5173
2. **上传图片**：点击上传区域或拖拽图片到指定区域
3. **解析二维码**：点击「解析二维码」按钮
4. **查看结果**：显示解析内容和二维码类型

---

## 📄 许可证

本项目采用 MIT 许可证，详情请参见 LICENSE 文件。

---

**项目维护**：QR Code Analyzer Team  
**最后更新**：2026-05-28
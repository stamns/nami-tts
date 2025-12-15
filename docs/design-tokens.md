# Design Tokens（前端样式变量）

本项目的前端 UI（`frontend/index.html`）使用 CSS Custom Properties（`--token`）来统一管理颜色、间距、圆角、阴影和字号。

目标：
- **不要在组件/选择器里写死颜色、padding、gap、radius、font-size**。
- 统一从 `:root` token 引用，确保全局一致、可主题化、可维护。

> Token 定义位置：`frontend/index.html` → `<style>` → `:root { ... }`

---

## 1. 调色板（Purple / Orange 系统）

### Brand（品牌色）
- `--color-primary`：主色紫（背景基调），对应 **#201024**
- `--color-primary-500`：亮紫（高亮/渐变的紫端）
- `--color-accent`：点缀橙（强调/渐变的橙端），对应 **#f97316**

### Semantic（语义色）
用于状态提示（不要用 brand 色冒充语义色）：
- `--color-success`：成功/可用
- `--color-danger`：错误/失败
- `--color-info`：信息/提示（偏暖色）

同时提供了状态块配套的背景/边框 token：
- `--status-*-bg`
- `--status-*-border`

### Neutrals（中性色）
`--rgb-neutral-*` 为基础中性色（RGB 三元组），用于构建带透明度的文本、边框、surface 等。

---

## 2. Surface / Border / Text

常用层级：
- `--surface-card`：卡片底色
- `--surface-neutral-*`：弱背景（用于按钮、提示块、列表项等）
- `--surface-glass-*`：玻璃拟态（header 等）

文本：
- `--color-text`：正文
- `--color-text-muted` / `--color-text-subtle`：次级文字
- `--color-text-on-dark*`：深色背景上的文字

边框：
- `--border-neutral-*`
- `--border-on-dark-*`

---

## 3. 间距（8px Grid）

间距以 8px 网格为主：
- `--space-2 = 0.5rem`（8px）
- `--space-3 = 1rem`（16px）
- `--space-4 = 1.5rem`（24px）
- `--space-5 = 2rem`（32px）

并保留半步用于紧凑场景：
- `--space-1 = 0.25rem`（4px）

原则：
- 布局的 `gap / padding / margin` 优先使用 `--space-*`。
- 不新增散落的 `px`/`rem` 常量。

---

## 4. 圆角与阴影

圆角：
- `--radius-sm / --radius-md / --radius-lg / --radius-xl`
- `--radius-pill`：胶囊/进度条

阴影：
- `--shadow-card`
- `--shadow-modal`

---

## 5. 排版（Typography）

字号使用 `clamp()` 以适配不同屏幕：
- `--font-size-xs / sm / md / lg`

行高：
- `--line-height-tight / snug / normal`

---

## 6. 实用工具类（Utilities）

为避免 HTML 中出现 `style="..."`，提供了少量 utility：

### 布局
- `.cluster` + `.cluster-sm|.cluster-md`：横向排列（常用于按钮组）
- `.wrap`：允许换行
- `.stack` + `.stack-sm|.stack-md`：纵向排列
- `.mt-sm`：小的上边距

### 文字
- `.text-xs|.text-sm|.text-md|.text-lg`
- `.text-muted` / `.text-subtle`

使用建议：
- **能用 token 就用 token**（写在组件选择器里）
- **必须在 HTML 上表达布局时**（例如按钮组/选项组），优先使用 utility class，而不是 inline style。

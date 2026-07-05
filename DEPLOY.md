# MindMirror 腾讯云部署手册

## 一、购买服务器

### 推荐配置

| 项目 | 推荐 |
|------|------|
| 产品 | 腾讯云轻量应用服务器 (Lighthouse) |
| 配置 | 2核4G / 5M带宽 / 60G SSD / 500G流量 |
| 系统镜像 | Ubuntu 22.04 LTS |
| 地域 | 上海 / 广州 / 北京（选离你近的） |
| 时长 | 1年 |

### 购买链接

根据你的用户身份选择：

- **新用户（个人，产品首单）**：
  - 秒杀 4核4G ¥38/年：https://cloud.tencent.com/act/pro/featured-202604
  - OpenClaw 2核4G ¥188/年（续费同价）：https://cloud.tencent.com/act/pro/openclaw
  
- **老用户（新老同享）**：
  - 同价续费 2核4G ¥199/年：https://cloud.tencent.com/act/lighthouse_care
  
- **免费试用（体验用）**：
  - 0元体验1个月：https://cloud.tencent.com/act/pro/free

> 建议：如果你是个人新用户，优先抢 ¥38 秒杀（4核4G），抢不到选 ¥188 的 OpenClaw 2核4G（续费同价）。

---

## 二、服务器初始化

购买后，在腾讯云控制台找到你的轻量应用服务器，记下**公网IP**。

### 2.1 SSH 登录服务器

```bash
ssh root@<你的服务器IP>
```

首次登录会让你设置密码，或者在控制台 → 重置密码。

### 2.2 安装 Docker & Docker Compose

```bash
# 更新系统
apt update && apt upgrade -y

# 安装 Docker（官方脚本）
curl -fsSL https://get.docker.com | bash

# 启动并设置开机自启
systemctl start docker
systemctl enable docker

# 验证安装
docker --version
docker compose version
```

### 2.3 安装 Git

```bash
apt install -y git
```

### 2.4 配置 HuggingFace 镜像（重要！）

国内服务器访问 HuggingFace 可能超时，需要设置镜像：

```bash
# 全局配置 HF 镜像
echo 'export HF_ENDPOINT=https://hf-mirror.com' >> /etc/environment
source /etc/environment
```

---

## 三、部署项目

### 3.1 克隆代码

```bash
cd /opt
git clone https://github.com/<你的用户名>/MindMirror.git mindmirror
cd /opt/mindmirror
```

### 3.2 配置环境变量

```bash
cp .env.example .env
nano .env
```

填入你的 Anthropic API Key：

```
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

如果需要使用 Claude API 代理（国内加速），也在这里配置 `ANTHROPIC_BASE_URL`。

### 3.3 启动服务

```bash
docker compose up -d --build
```

首次构建需要 5~10 分钟（下载 PyTorch + 嵌入模型），后续重启很快。

### 3.4 验证部署

```bash
# 检查容器状态
docker compose ps

# 检查后端健康
curl http://localhost/api/health
# 应返回 {"status":"ok"}

# 查看日志
docker compose logs -f backend
```

### 3.5 访问产品

浏览器打开 `http://<你的服务器IP>`，即可看到 MindMirror 前端页面。

---

## 四、开放防火墙端口

在腾讯云控制台：

1. 进入「轻量应用服务器」→ 选中你的实例
2. 点击「防火墙」标签
3. 添加规则：
   - 端口：**80**（HTTP）
   - 协议：TCP
   - 来源：0.0.0.0/0

如果后续绑定域名并配置 HTTPS，还需要开放 **443** 端口。

---

## 五、配置 GitHub Actions 自动部署

### 5.1 服务器生成 SSH 密钥

```bash
# 在服务器上生成密钥（一路回车）
ssh-keygen -t ed25519 -C "github-actions-deploy"

# 将公钥加入 authorized_keys
cat ~/.ssh/id_ed25519.pub >> ~/.ssh/authorized_keys

# 查看私钥（下一步要用）
cat ~/.ssh/id_ed25519
```

### 5.2 配置 GitHub Secrets

在你的 GitHub 仓库页面：

1. 进入 `Settings` → `Secrets and variables` → `Actions`
2. 添加以下 3 个 Secret：

| Name | Value |
|------|-------|
| `SERVER_HOST` | 你的服务器公网 IP |
| `SERVER_USER` | `root` |
| `SERVER_SSH_KEY` | 上一步获得的私钥内容（完整复制） |

### 5.3 使用

配置完成后，每次 push 到 `main` 分支就会自动触发部署：

```bash
git add .
git commit -m "feat: some change"
git push origin main
```

在 GitHub 仓库的 `Actions` 标签页可以看到部署进度和日志。

---

## 六、可选：绑定域名

如果你有域名，可以绑定并配置 HTTPS：

### 6.1 域名解析

在你的域名服务商处，添加 A 记录指向服务器 IP。

### 6.2 安装 Certbot 获取免费 SSL 证书

```bash
apt install -y certbot
certbot certonly --standalone -d yourdomain.com
```

### 6.3 修改 Nginx 配置支持 HTTPS

将 `nginx/default.conf` 改为监听 443 并加载证书，80 端口重定向到 HTTPS。这一步可以后续按需配置。

---

## 七、日常运维

### 查看日志

```bash
cd /opt/mindmirror
docker compose logs -f            # 所有服务
docker compose logs -f backend    # 仅后端
docker compose logs -f frontend   # 仅前端
```

### 重启服务

```bash
docker compose restart
```

### 手动更新部署

```bash
cd /opt/mindmirror
git pull origin main
docker compose up -d --build
docker image prune -f
```

### 备份数据

```bash
# 备份 SQLite 数据库和 FAISS 索引
docker cp mindmirror-backend:/app/data ./backup_$(date +%Y%m%d)
```

---

## 八、费用总结

| 项目 | 费用 |
|------|------|
| 腾讯云轻量 2核4G/1年 | ¥188（OpenClaw 续费同价） |
| 域名（可选） | ¥0~50/年 |
| Claude API 调用 | 按实际用量计费 |
| **总计** | **¥188/年 + API 费用** |

比 Railway 后端每月 $5~20 的方案便宜很多，且国内面试官直接访问无需 VPN。

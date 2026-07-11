# MindMirror 腾讯云部署

生产环境使用 Docker Compose。每次推送 `main` 后，GitHub Actions 会先验证前端构建和后端语法，再通过 SSH 上传源码到腾讯云，利用 Docker 层缓存构建并重启服务，最后检查 `/api/health`。

## 一次性服务器准备

```bash
sudo mkdir -p /opt/mindmirror
sudo chown -R ubuntu:ubuntu /opt/mindmirror
sudo install -m 600 /dev/null /opt/mindmirror/.env
```

使用编辑器在 `/opt/mindmirror/.env` 中至少配置：

```dotenv
ANTHROPIC_API_KEY=your-key
ANTHROPIC_BASE_URL=
CORS_ORIGIN=
ADMIN_TOKEN=
```

`ADMIN_TOKEN` 留空时，开发者统计接口默认返回 404。生产环境的 `.env` 只保存在服务器，不上传到 GitHub。

## GitHub Actions Secrets

在仓库的 `Settings → Secrets and variables → Actions` 中配置：

- `SERVER_HOST`：腾讯云公网 IP 或已备案域名
- `SERVER_USER`：建议为 `ubuntu`
- `SERVER_SSH_KEY`：仅用于部署的 SSH 私钥

对应公钥需要写入服务器用户的 `~/.ssh/authorized_keys`。

## 发布与检查

推送 `main` 会自动发布，也可以在 Actions 页面手动运行 `Verify and deploy to Tencent Cloud`。

服务器检查命令：

```bash
cd /opt/mindmirror
docker compose ps
docker compose logs --tail=100
curl --fail http://127.0.0.1/api/health
```

健康检查应返回：

```json
{"status":"ok"}
```

## 域名与 HTTPS

域名完成 ICP 备案并解析到服务器后，再开放 443 并部署证书。HTTPS 稳定前不要启用 HSTS；证书和私钥不得提交到仓库。

# 网络入侵检测与防御系统

这是一个基于Python的网络入侵检测与防御系统，提供实时流量分析、攻击检测、自动防御和可视化监控功能。

## 功能特点

- **流量检测**：实时捕获和分析网络流量，识别可疑活动和异常行为
- **入侵防御**：检测并拦截恶意流量，保护网络免受攻击和未授权访问
- **告警响应**：针对检测到的威胁生成警报，并执行自动响应措施
- **网络监控**：可视化网络状态与攻击统计，为安全分析提供实时数据
- **友好界面**：直观的Web界面，提供流量统计、攻击日志和系统设置

## 系统架构

系统由以下几个核心模块组成：

1. **流量检测模块**：负责捕获和分析网络流量，识别可疑活动
2. **入侵防御模块**：根据检测结果执行防御措施，如阻止恶意IP
3. **告警响应模块**：管理和发送告警通知，记录安全事件
4. **网络监控模块**：收集网络统计数据，提供可视化界面
5. **Web界面**：用户交互界面，展示系统状态和控制系统功能

## 技术栈

- **后端**：Python, Flask, Flask-SocketIO, Scapy
- **前端**：HTML5, CSS3, JavaScript, Bootstrap, Chart.js
- **数据库**：MongoDB（用于存储日志和配置）
- **容器化**：Docker, Docker Compose

## 快速开始

### 先决条件

- Python 3.9+
- Docker 和 Docker Compose（可选，用于容器化部署）
- 网络接口访问权限（需要root/管理员权限）

### 安装方法

1. 克隆仓库：

```bash
git clone https://github.com/yourusername/intrusion_detection_system.git
cd intrusion_detection_system
```

2. 安装依赖：

```bash
pip install -r requirements.txt
```

3. 运行系统：

```bash
cd app
python app.py
```

### 使用Docker部署

1. 构建和启动容器：

```bash
docker-compose -f docker/docker-compose.yml up -d
```

2. 访问系统：

打开浏览器，访问 `http://localhost:5000`

## 配置指南

系统提供了多种配置选项，可通过Web界面或配置文件进行修改：

- **常规设置**：系统名称、网络接口、日志保留时间等
- **检测设置**：检测模式、数据包采样率、深度数据包检测等
- **防御设置**：防御模式、IP阻止持续时间、阻止阈值等
- **告警设置**：Web通知、邮件通知、最低告警级别等
- **网络设置**：管理界面端口、监控网络范围、SSL/TLS等

## 系统截图

![仪表盘](docs/images/dashboard.png)
*系统仪表盘，显示实时流量和威胁检测*

![日志页面](docs/images/logs.png)
*攻击日志和系统事件记录*

![设置页面](docs/images/settings.png)
*系统配置和管理*

## 注意事项

- 系统需要网络接口访问权限，建议以管理员权限运行
- 在生产环境中使用前，请确保已正确配置安全设置
- 系统设计用于教育和研究目的，请遵守相关法律法规
- 默认情况下，系统使用模拟模式运行防御功能，如需激活实际防御，需要根据实际环境配置

## 贡献指南

欢迎贡献代码、报告问题或提出改进建议。请通过以下方式参与：

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

## 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 联系方式

如有任何问题或建议，请通过以下方式联系我：

- 电子邮件：your.email@example.com
- 项目Issues：[GitHub Issues](https://github.com/yourusername/intrusion_detection_system/issues)

---

**免责声明**：本系统仅供教育和研究目的使用。作者不对系统的使用或滥用导致的任何损失或损害负责。使用者应自行承担使用风险，并确保遵守相关法律法规。

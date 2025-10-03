[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

# 恒大物业 Home Assistant 集成

通过抓包恒大智慧社区 APP 获取用户认证信息，实现对恒大物业费用的自动化监控和管理。

## 功能特点

🏠 **多维度费用监控**
- 已交物业费、预交物业费、待交物业费
- 7种详细费用分类
- 智能数据聚合和统计

📊 **智能统计功能**
- 预交费用合计
- 月公摊费统计
- 待交费用合计
- 实时更新时间显示

🗓️ **灵活时间配置**
- 支持年度数据查询
- 可配置查询年份
- 自动数据更新

## 安装方法

### HACS 安装（推荐）
1. 在 HACS 中添加自定义仓库
2. 搜索 "恒大物业" 集成
3. 点击安装
4. 重启 Home Assistant

### 手动安装
1. 下载最新版本
2. 将 `hengda_property` 文件夹复制到 `config/custom_components` 目录
3. 重启 Home Assistant

## 配置说明

### 获取认证信息
使用抓包工具获取恒大智慧社区 APP 的以下信息：
- `unionId`
- `authorization`

### 集成配置
1. 进入 Home Assistant → 配置 → 集成
2. 添加 "恒大物业" 集成
3. 输入认证信息和查询年份

## 支持的实体

| 设备类型 | 实体数量 | 主要功能 |
|---------|---------|---------|
| 已交物业费 | 9个实体 | 显示已缴纳的各项费用 |
| 预交物业费 | 9个实体 | 显示预存费用余额 |
| 待交物业费 | 9个实体 | 显示待缴纳费用 |

## 技术细节

- **数据源**: 恒大智慧社区官方 API
- **更新频率**: 每小时自动更新
- **认证方式**: Token 认证
- **支持版本**: Home Assistant 2023.8.0+

## 注意事项

⚠️ **重要提示**
- 认证信息需要定期更新
- 仅支持个人非商业使用
- 需要稳定的网络连接

## 故障排除

常见问题请参考 [GitHub Issues](https://github.com/lambilly/hengda_property/issues) 或提交新的 Issue。

## 更新日志

### v1.0.0
- 初始版本发布
- 支持三种费用类型监控
- 提供合计统计功能
- 年度数据查询支持

---

**开发者**: lambilly  
**许可证**: MIT License  
**支持**: [GitHub Repository](https://github.com/lambilly/hengda_property)

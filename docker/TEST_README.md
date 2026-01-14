# Docker 环境测试脚本

这些脚本用于验证 SWE-bench Docker 环境是否正常工作。

## 脚本说明

### test_docker_env.sh

测试单个 Docker 镜像的环境配置。

**功能检查：**
1. 镜像是否存在
2. 容器是否能正常启动
3. Conda 环境是否配置正确
4. 工作目录 `/testbed` 是否存在
5. 测试框架是否可用（自动检测 Django/pytest/unittest）

**用法：**

```bash
# 测试基础镜像
./docker/test_docker_env.sh --image swebench/sweb.eval.x86_64.django_1776_django-11099

# 测试 Agent 镜像
./docker/test_docker_env.sh --image swebench/sweb.eval.x86_64.django_1776_django-11099 --agent
```

### test_all_images.sh

批量测试多个 Docker 镜像。

**用法：**

```bash
# 测试前 5 个镜像（默认）
./docker/test_all_images.sh

# 测试前 3 个镜像
./docker/test_all_images.sh --max 3

# 测试所有镜像
./docker/test_all_images.sh --all

# 测试 Agent 版本的镜像
./docker/test_all_images.sh --agent --max 3
```

## 环境要求

- Docker 已安装并运行
- 已构建 SWE-bench 镜像（参考 `image_list.txt`）
- Bash shell 环境

## 测试输出

脚本会输出彩色的测试结果：
- ✓ 绿色：测试通过
- ✗ 红色：测试失败
- ⚠ 黄色：警告信息

## 镜像列表

所有可用的镜像列在 `docker/image_list.txt` 文件中。

## 环境配置

每个 SWE-bench 容器包含：
- **工作目录**: `/testbed` - 包含项目源代码
- **Conda 环境**: `testbed` - 位于 `/opt/miniconda3/envs/testbed`
- **测试框架**: 根据项目类型自动配置（Django/pytest/unittest）

## 示例

```bash
# 快速测试 Django 项目
./docker/test_docker_env.sh --image swebench/sweb.eval.x86_64.django_1776_django-11099

# 快速测试 pytest 项目
./docker/test_docker_env.sh --image swebench/sweb.eval.x86_64.pytest-dev_1776_pytest-7168

# 批量测试前 10 个镜像
./docker/test_all_images.sh --max 10
```

## 故障排查

如果测试失败，检查：
1. Docker 服务是否运行：`docker ps`
2. 镜像是否存在：`docker images | grep swebench`
3. 磁盘空间是否充足：`df -h`
4. 容器日志：查看 `docker/build_logs/` 目录

#!/bin/bash

# 备份脚本：将 output 目录备份到 backup 目录下

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SOURCE_DIR="$SCRIPT_DIR/output"
BACKUP_DIR="$SCRIPT_DIR/backup"

# 检查 output 目录是否存在
if [ ! -d "$SOURCE_DIR" ]; then
    echo "错误: output 目录不存在"
    exit 1
fi

# 创建带时间戳的备份目录
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
TARGET_DIR="$BACKUP_DIR/output_$TIMESTAMP"

mkdir -p "$TARGET_DIR"
cp -r "$SOURCE_DIR"/* "$TARGET_DIR"/

echo "备份完成: $TARGET_DIR"

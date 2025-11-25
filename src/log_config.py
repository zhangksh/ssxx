import logging
from logging.handlers import TimedRotatingFileHandler
import os

# 创建logs目录
os.makedirs('logs', exist_ok=True)

#  每天午夜自动轮转
logging.basicConfig(
    handlers=[
        TimedRotatingFileHandler(
            'logs/app.log',      # 基础文件名
            when='midnight',     # 每天午夜轮转
            interval=1,          # 间隔1天
            backupCount=14,       # 保留7个备份
            encoding='utf-8'
        )
    ],
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
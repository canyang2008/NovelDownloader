import os
from dataclasses import dataclass


@dataclass
class BackupConfig:
    auto: bool = False
    interval: int = 86400
    backup_dir: str = os.path.join(os.path.expanduser('~'),"novel_backup")
    name: str = "Novel_backup.zip"
    last_time: float = -1
    compression: int = 0
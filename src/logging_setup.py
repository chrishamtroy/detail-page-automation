"""loguru 로깅 초기화."""
import sys
from pathlib import Path
from loguru import logger


def setup(output_dir: Path) -> None:
    """콘솔 + 파일 싱크를 설정한다. generate.py에서 1회 호출."""
    logger.remove()

    # 콘솔: INFO 이상, 간결한 포맷
    logger.add(
        sys.stderr,
        level="INFO",
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <7}</level> | {message}",
        colorize=True,
    )

    # 파일: DEBUG 이상, 풀 포맷
    log_path = output_dir / "run.log"
    logger.add(
        str(log_path),
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <7} | {name}:{line} | {message}",
        encoding="utf-8",
        rotation=None,
    )

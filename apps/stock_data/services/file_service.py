import logging
from pathlib import Path

from django.conf import settings

LOG_PREFIX = "[File Service]"
logger = logging.getLogger(__name__)


class FileService:
    @staticmethod
    def save_content(content, local_filename, binary: bool = False):
        file_path = Path(settings.MEDIA_ROOT) / local_filename

        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)

            mode = "wb" if binary else "w"
            kwargs = {"encoding": "utf-8"} if not binary else {}

            with open(file_path, mode, **kwargs) as f:
                f.write(content)

            logger.info("%s Saved: %s", LOG_PREFIX, file_path)

        except OSError as e:
            logger.error("%s Failed to save file %s: %s", LOG_PREFIX, file_path, e)
            if file_path.exists():
                file_path.unlink()  # remove uncomplete file

            return None
        return True

    @staticmethod
    def read_content(local_filename, binary: bool = False):
        file_path = Path(settings.MEDIA_ROOT) / local_filename

        # 1. Sprawdzenie czy plik istnieje (uprzedzamy błąd OSError)
        if not file_path.is_file():
            logger.warning("%s File not found: %s", LOG_PREFIX, file_path)
            return None

        try:
            mode = "rb" if binary else "r"
            kwargs = {"encoding": "utf-8"} if not binary else {}

            with open(file_path, mode, **kwargs) as f:
                content = f.read()

            logger.info("%s Read successful: %s", LOG_PREFIX, file_path)
            return content

        except PermissionError:
            logger.error("%s Permission denied: %s", LOG_PREFIX, file_path)
            return None

        except OSError as e:
            logger.error("%s Failed to read file %s: %s", LOG_PREFIX, file_path, e)
            return None

    @staticmethod
    def delete_file(local_filename):
        file_path = Path(settings.MEDIA_ROOT) / local_filename

        try:
            if file_path.is_file():
                file_path.unlink()
                logger.info("%s Deleted file: %s", LOG_PREFIX, file_path)
                return True
            else:
                logger.warning("%s File not found for deletion: %s", LOG_PREFIX, file_path)
                return False

        except PermissionError as e:
            logger.error("%s Permission denied when deleting file %s: %s", LOG_PREFIX, file_path, e)
            return False

        except OSError as e:
            logger.error("%s Failed to delete file %s: %s", LOG_PREFIX, file_path, e)
            return False

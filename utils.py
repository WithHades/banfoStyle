import time


def getUuid() -> int:
    # 13位时间戳充当一个uuid
    return int(round(time.time() * 1000))
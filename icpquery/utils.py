import asyncio
import time
from typing import Callable

from .captcha import fuck_captcha
from .dto import AsyncIcpQueryDto
from .exceptions import FuckCaptchaFail


async def resolve_captcha(
    dto: AsyncIcpQueryDto,
    callback: Callable[[int], None] = None,
    max_retry: int = 10,
    fail_delay: float = 1.0,
):
    for retry_cnt in range(max_retry):
        if callable(callback):
            callback(retry_cnt)

        captcha = await dto.fetch_captcha()
        try:
            points = await asyncio.to_thread(fuck_captcha, captcha)
        except FuckCaptchaFail:
            time.sleep(fail_delay)
            continue

        if await dto.check_captcha(points):
            return

        time.sleep(fail_delay)

    raise FuckCaptchaFail

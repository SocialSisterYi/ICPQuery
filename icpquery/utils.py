import asyncio
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
    """自动处理验证码
    Args:
        dto: ICP查询Dto对象
        callback: 验证码识别回调
        max_retry: 验证码识别最大重试次数
        fail_delay: 验证码识别失败重试等待时间
    """
    for retry_cnt in range(max_retry):
        if callable(callback):
            callback(retry_cnt)

        captcha = await dto.get_captcha()
        try:
            points = await asyncio.to_thread(fuck_captcha, captcha)
        except FuckCaptchaFail:
            await asyncio.sleep(fail_delay)
            continue

        if await dto.check_captcha(points):
            return

        await asyncio.sleep(fail_delay)

    raise FuckCaptchaFail

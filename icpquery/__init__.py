from typing import Callable

from .dto import AsyncIcpQueryDto
from .exceptions import APIError, FuckCaptchaFail, ICPQueryError
from .schema import BeianQueryResp, SearchType
from .utils import resolve_captcha

__init__ = '1.0.0'

async def query(
    keyword: str,
    search_type: SearchType = SearchType.DOMAIN,
    captcha_cb: Callable[[int], None] = None,
    captcha_max_retry: int = 10,
    captcha_fail_delay: float = 1.0,
) -> BeianQueryResp:
    """调用ICP查询处理
    Args:
        keyword: 关键词
        search_type: 搜索类型
        captcha_cb: 验证码识别回调
        captcha_max_retry: 验证码识别最大重试次数
        captcha_fail_delay: 验证码识别失败重试等待时间
    Returns:
        BeianQueryResp: 查询结果
    """
    async with AsyncIcpQueryDto() as dto:
        await dto.get_token()
        await resolve_captcha(dto, captcha_cb, captcha_max_retry, captcha_fail_delay)
        results = await dto.query(keyword, search_type)
    return results

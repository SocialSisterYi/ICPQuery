from typing import Callable

from .dto import AsyncIcpQueryDto
from .exceptions import APIError, FuckCaptchaFail, ICPQueryError
from .schema import BeianQueryResp, SearchType
from .utils import resolve_captcha


async def query(
    keyword: str,
    search_type: SearchType = SearchType.DOMAIN,
    captcha_cb: Callable[[int], None] = None,
    captcha_max_retry: int = 10,
    captcha_fail_delay: float = 1.0,
) -> BeianQueryResp:
    async with AsyncIcpQueryDto() as dto:
        await dto.get_token()
        await resolve_captcha(dto, captcha_cb, captcha_max_retry, captcha_fail_delay)
        results = await dto.query(keyword, search_type)
    return results

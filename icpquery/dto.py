import json
import time
import uuid
from hashlib import md5
from types import TracebackType
from typing import Optional

import httpx

from .exceptions import APIError
from .schema import (
    BeianAPP,
    BeianQueryResp,
    BeianSite,
    CaptchaModule,
    Points,
    SearchType,
)

API_BASE = "https://hlwicpfwc.miit.gov.cn/icpproject_query/api"


class AsyncIcpQueryDto:
    client: httpx.AsyncClient
    client_id: str
    token: str
    refresh: str
    captcha: CaptchaModule
    captcha_key: str

    def __init__(
        self,
        client_id: Optional[str] = None,
        token: Optional[str] = None,
        refresh: Optional[str] = None,
    ) -> None:
        self.client = httpx.AsyncClient(
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0",
                "Referer": "https://beian.miit.gov.cn/",
                "Origin": "https://beian.miit.gov.cn",
            },
            follow_redirects=True,
            base_url=API_BASE,
        )
        self.token = token
        self.refresh = refresh
        if not client_id:
            self.client_id = str(uuid.uuid4())
        else:
            self.client_id = client_id

    async def __aenter__(self):
        await self.client.__aenter__()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None = None,
        exc_value: BaseException | None = None,
        traceback: TracebackType | None = None,
    ):
        await self.client.__aexit__()

    async def get_token(self, account: str = "test", secret: str = "test"):
        """获取Session Token
        Args:
            account:
            secret:
        """
        ts = int(time.time() * 1000)
        resp = await self.client.post(
            "/auth",
            data={
                "authKey": md5(f"{account}{secret}{ts}".encode()).hexdigest(),
                "timeStamp": str(ts),
            },
        )
        resp.raise_for_status()
        json_content = resp.json()
        if (code := json_content["code"]) != 200:
            raise APIError(code, json_content["msg"])
        json_content = json_content["params"]

        self.token = json_content["bussiness"]
        self.refresh = json_content["refresh"]

    async def refresh_token(self):
        """刷新Session Token"""
        resp = await self.client.get(
            "/auth/refresh",
            params={
                "refreshToken": self.refresh,
            },
        )
        resp.raise_for_status()
        json_content = resp.json()
        if (code := json_content["code"]) != 200:
            raise APIError(code, json_content["msg"])
        json_content = json_content["params"]

        self.token = json_content["bussiness"]
        self.refresh = json_content["refresh"]

    async def get_captcha(self) -> CaptchaModule:
        """获取图形验证码
        Returns:
            CaptchaModule: 图形验证码数据
        """
        resp = await self.client.post(
            "/image/getCheckImagePoint",
            headers={
                "Token": self.token,
            },
            json={
                "clientUid": f"point-{self.client_id}",
            },
        )
        resp.raise_for_status()
        json_content = resp.json()
        if (code := json_content["code"]) != 200:
            raise APIError(code, json_content["msg"])

        self.captcha = CaptchaModule.model_validate(json_content["params"])
        return self.captcha

    async def check_captcha(self, points: Points) -> bool:
        """提交图形验证码答案
        Args:
            points: 验证码点选坐标集
        Returns:
            bool: 是否校验通过
        """
        resp = await self.client.post(
            "/image/checkImage",
            headers={
                "Token": self.token,
            },
            json={
                "clientUid": self.client_id,
                "pointJson": points.dump_in_encrypt(self.captcha.secret_key),
                "secretKey": self.captcha.secret_key,
                "token": self.captcha.uuid,
            },
        )
        resp.raise_for_status()
        json_content = resp.json()
        if (code := json_content["code"]) != 200:
            raise APIError(code, json_content["msg"])

        if json_content.get("success"):
            self.captcha_key = json_content["params"]["sign"]
            return True
        return False

    async def query(
        self,
        keyword: str,
        search_type: SearchType,
        pn: int = 0,
        ps: int = 20,
    ) -> BeianQueryResp:
        """通过关键字查询ICP记录
        Args:
            keyword: 关键字
            search_type: 搜索类型
            pn: 页码
            ps: 每页数量
        Returns:
            BeianQueryResp: 查询结果
        """
        resp = await self.client.post(
            "/icpAbbreviateInfo/queryByCondition",
            headers={
                "token": self.token,
                "sign": self.captcha_key,
                "uuid": self.captcha.uuid,
                "Content-Type": "application/json",
            },
            # 防止403
            content=json.dumps(
                {
                    "pageNum": pn,
                    "pageSize": ps,
                    "unitName": keyword,
                    "serviceType": search_type.value,
                },
                separators=(",", ":"),
            ),
        )
        resp.raise_for_status()
        json_content = resp.json()
        if (code := json_content["code"]) != 200 or not json_content["success"]:
            raise APIError(code, json_content["msg"])
        json_content = json_content["params"]

        if search_type == SearchType.DOMAIN:
            result = [BeianSite.model_validate(r) for r in json_content["list"]]
        elif search_type == SearchType.APP:
            result = [BeianAPP.model_validate(r) for r in json_content["list"]]

        return BeianQueryResp(search_type=search_type, results=result)

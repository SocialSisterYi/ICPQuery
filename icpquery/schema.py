import base64
from datetime import datetime
from enum import Enum
from typing import Sequence

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from pydantic import BaseModel, Field, RootModel
from rich.columns import Columns
from rich.console import Console, ConsoleOptions, RenderResult
from rich.table import Table


class SearchType(Enum):
    """搜索类型"""

    DOMAIN = 1  # 域名
    APP = 6  # APP
    MINI_PROG = 7  # 小程序
    FAST_PROG = 8  # 快应用


class CpatchaBackguard(Enum):
    """验证码背景类型"""

    海滩 = "beach"
    蝴蝶与花 = "butterfly_flower"
    蝴蝶 = "butterfly"
    蛋糕 = "cake"
    相机 = "camera"
    汽车 = "car"
    猫 = "cats"
    娃娃 = "doll"
    落叶 = "falls"
    蚂蚱 = "grasshopper"
    草原 = "grassland"
    马 = "horse"
    马群 = "horse_herd"
    蜂鸟 = "hummingbird"
    月球 = "moon"
    派 = "pie"
    月季 = "rose"
    雪山 = "snow_mountain"
    松鼠 = "squirrel"
    别墅 = "villa"
    墙 = "wall"


class CaptchaModule(BaseModel):
    """Captcha数据"""

    background_img: str = Field(alias="bigImage", description="背景图片")
    secret_key: str = Field(alias="secretKey", description="加密密钥")
    pointer_img: str = Field(alias="smallImage", description="文字图片")
    uuid: str
    word_count: int = Field(alias="wordCount", description="点选文字数")

    def get_bg_img(self):
        return base64.b64decode(self.background_img)

    def get_ptr_img(self):
        return base64.b64decode(self.pointer_img)


class Pos(BaseModel):
    x: int
    y: int


class Points(RootModel):
    """点选坐标集"""

    root: list[Pos] = Field([])

    def dump_in_encrypt(self, key: str) -> str:
        cryptor = AES.new(key.encode(), AES.MODE_ECB)
        return base64.b64encode(cryptor.encrypt(pad(self.model_dump_json().encode(), 16))).decode()

    def append(self, x: int, y: int):
        self.root.append(Pos(x=x, y=y))

    @classmethod
    def from_list(cls, lst: list[Sequence]):
        obj = cls()
        for x, y in lst:
            obj.append(x, y)
        return obj


class BeianSite(BaseModel):
    """网站备案查询结果"""

    content_type_name: str = Field(alias="contentTypeName", description="前置审批项")
    domain: str = Field(description="网站域名")
    domain_id: int = Field(alias="domainId", description="域名id")
    leader_name: str = Field(alias="leaderName")
    limit_access: str = Field(alias="limitAccess", description="限制接入")
    main_id: int = Field(alias="mainId", description="主体备案id")
    main_licence: str = Field(alias="mainLicence", description="主体备案号")
    nature_name: str = Field(alias="natureName", description="主办单位性质")
    service_id: int = Field(alias="serviceId", description="ICP备案id")
    service_licence: str = Field(alias="serviceLicence", description="ICP备案号")
    unit_name: str = Field(alias="unitName", description="主体名称")
    update_record_time: datetime = Field(alias="updateRecordTime", description="审核通过日期")


class BeianAPP(BaseModel):
    """APP备案查询结果"""

    city_id: int = Field(alias="cityId", description="")
    county_id: int = Field(alias="countyId", description="")
    data_id: int = Field(alias="dataId", description="")
    leader_name: str = Field(alias="leaderName", description="企业代表")
    main_licence: str = Field(alias="mainLicence", description="")
    main_unit_address: str = Field(alias="mainUnitAddress", description="单位地址")
    main_unit_cert_no: str = Field(alias="mainUnitCertNo", description="")
    main_unit_cert_cype: int = Field(alias="mainUnitCertType", description="")
    nature_id: int = Field(alias="natureId", description="")
    province_id: int = Field(alias="provinceId", description="")
    service_name: str = Field(alias="serviceName", description="APP名称")
    service_type: int = Field(alias="serviceType", description="")
    version: str = Field(description="")

    content_type_name: str = Field(alias="contentTypeName", description="前置审批项")
    main_id: int = Field(alias="mainId", description="主体备案id")
    main_licence: str = Field(alias="mainLicence", description="主体备案号")
    nature_name: str = Field(alias="natureName", description="主办单位性质")
    service_id: int = Field(alias="serviceId", description="ICP备案id")
    service_licence: str = Field(alias="serviceLicence", description="ICP备案号")
    unit_name: str = Field(alias="unitName", description="主体名称")
    update_record_time: datetime = Field(alias="updateRecordTime", description="审核通过日期")


class BeianQueryResp(BaseModel):
    search_type: SearchType = Field(serialization_alias="searchType")
    results: list[BeianSite | BeianAPP]

    def __bool__(self):
        return len(self.results) > 0

    def __iter__(self):
        return iter(self.results)

    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        col = Columns()
        for result in self.results:
            tb = Table(show_header=False)
            if self.search_type == SearchType.DOMAIN:
                tb.add_row("[green]网站域名", result.domain)
                tb.add_row("[green]备案号", result.service_licence)
                tb.add_row("[green]主体名称", result.unit_name)
                tb.add_row("[green]主体性质", result.nature_name)
                tb.add_row("[green]主体备案号", result.main_licence)
                tb.add_row("[green]限制接入", result.limit_access)
            elif self.search_type == SearchType.APP:
                tb.add_row("[green]APP名称", result.service_name)
                tb.add_row("[green]备案号", result.service_licence)
                tb.add_row("[green]前置审批项", result.content_type_name)
                tb.add_row("[green]主体名称", result.unit_name)
                tb.add_row("[green]主体性质", result.nature_name)
                tb.add_row("[green]主体代表", result.leader_name)
                tb.add_row("[green]主体地址", result.main_unit_address)
                tb.add_row("[green]主体备案号", result.main_licence)
            tb.add_row(
                "[green]通过日期",
                result.update_record_time.strftime("%Y-%m-%d %H:%M:%S"),
            )
            col.add_renderable(tb)
        yield col

    def to_json(self) -> str:
        return self.model_dump_json(by_alias=True)

    def to_text(self, kv_delimiter=": ", record_delimiter="-" * 20) -> str:
        if self.results:
            lines = []
            for result in self.results:
                if self.search_type == SearchType.DOMAIN:
                    lines.append(("网站域名", result.domain))
                    lines.append(("备案号", result.service_licence))
                    lines.append(("主体名称", result.unit_name))
                    lines.append(("主体性质", result.nature_name))
                    lines.append(("主体备案号", result.main_licence))
                    lines.append(("限制接入", result.limit_access))
                elif self.search_type == SearchType.APP:
                    lines.append(("APP名称", result.service_name))
                    lines.append(("备案号", result.service_licence))
                    lines.append(("前置审批项", result.content_type_name))
                    lines.append(("主体名称", result.unit_name))
                    lines.append(("主体性质", result.nature_name))
                    lines.append(("主体代表", result.leader_name))
                    lines.append(("主体地址", result.main_unit_address))
                    lines.append(("主体备案号", result.main_licence))
                lines.append(
                    (
                        "通过日期",
                        result.update_record_time.strftime("%Y-%m-%d %H:%M:%S"),
                    )
                )
                lines.append((None, None))
            lines.pop()
            return "\n".join(f"{k}{kv_delimiter}{v}" if k is not None else record_delimiter for k, v in lines)
        else:
            return "未查询到该备案"

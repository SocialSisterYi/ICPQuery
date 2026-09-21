import base64
from enum import Enum, auto
from typing import Optional, Sequence

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from pydantic import BaseModel, Field, RootModel


class CaptchaType(Enum):
    """Captcha类型"""

    Click = auto()
    Slide = auto()


class CaptchaBase(BaseModel):
    background_img: str = Field(alias="bigImage", description="背景图片")
    pointer_img: str = Field(alias="smallImage", description="指示图片")
    uuid: str

    @property
    def bg_img_data(self) -> bytes:
        return base64.b64decode(self.background_img)

    @property
    def ptr_img_data(self) -> bytes:
        return base64.b64decode(self.pointer_img)


class CaptchaSlideModule(CaptchaBase):
    """滑动Captcha数据"""

    height: int = Field(description="滑块高度")


class CaptchaClickModule(CaptchaBase):
    """点选Captcha数据"""

    secret_key: str = Field(alias="secretKey", description="加密密钥")
    word_count: int = Field(alias="wordCount", description="点选文字数")


class CaptchaModule(BaseModel):
    """Captcha数据"""

    type: CaptchaType
    click: Optional[CaptchaClickModule] = Field(None)
    slide: Optional[CaptchaSlideModule] = Field(None)


class Pos(BaseModel):
    """坐标点"""

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
    def from_list(cls, lst: list[tuple[int, int]]):
        obj = cls([])
        for x, y in lst:
            obj.append(x, y)
        return obj


class CpatchaBackguard(Enum):
    """验证码背景类型"""

    篮子_1 = "basket1"
    篮子_2 = "basket2"
    海滩 = "beach"
    自行车 = "bike"
    麦田 = "corn_field"
    蝴蝶与花_1 = "butterfly_flower1"
    蝴蝶与花_2 = "butterfly_flower2"
    蝴蝶与花_3 = "butterfly_flower3"
    蝴蝶与花_4 = "butterfly_flower4"
    蝴蝶与花_5 = "butterfly_flower5"
    蝴蝶与花_6 = "butterfly_flower6"
    蝴蝶 = "butterfly"
    蛋糕 = "cake"
    相机 = "camera"
    汽车 = "car"
    猫_1 = "cat1"
    猫_2 = "cat2"
    猫_3 = "cat3"
    海岸公园 = "coast_park"
    娃娃 = "doll"
    落叶 = "falls"
    蚂蚱 = "grasshopper"
    马 = "horse"
    马群 = "horse_herd"
    蜂鸟 = "hummingbird"
    客厅_1 = "living_room1"
    客厅_2 = "living_room2"
    月球 = "moon"
    牵牛花 = "morning_glory"
    桃子 = "peach"
    派 = "pie"
    雨_1 = "rain1"
    雨_2 = "rain2"
    月季 = "rose"
    雪山 = "snow_mountain"
    松鼠_1 = "squirrel1"
    松鼠_2 = "squirrel2"
    石头 = "stone"
    别墅 = "villa"
    墙 = "wall"
    木材 = "woods"
    老虎 = "tiger"
    鹿 = "deer"
    飞机 = "plane"
    桥_1 = "bridge1"
    桥_2 = "bridge2"
    草地_1 = "grassland1"
    草地_2 = "grassland2"
    草地_3 = "grassland3"
    草地_4 = "grassland4"
    草地_5 = "grassland5"
    雪树 = "snow_tree"
    DNA = "dna"
    翼龙 = "pterosaur"
    木屋 = "wood_house"
    狮子 = "lion"
    城市 = "city"
    阁楼 = "attic"
    魔法 = "magic"
    山谷 = "valley"
    冰雪 = "snow"
    天鹅 = "swan"
    仙人球 = "cactus"
    鸭子_1 = "duck1"
    鸭子_2 = "duck2"
    大丽花_1 = "dahlia1"
    大丽花_2 = "dahlia2"
    菊花_1 = "chrysanthemum1"
    菊花_2 = "chrysanthemum2"
    树叶_1 = "leaves1"
    树叶_2 = "leaves2"
    树叶_3 = "leaves3"
    树叶_4 = "leaves4"
    狗尾草 = "foxtail_grass"
    蒲苇 = "pampas_grass"
    红百合_1 = "red_lily1"
    红百合_2 = "red_lily2"
    蜜蜂 = "bee"
    星夜 = "starry_night"

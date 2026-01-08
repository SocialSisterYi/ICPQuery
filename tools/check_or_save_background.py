import asyncio
import time
from pathlib import Path

import cv2
import numpy as np

from icpquery import AsyncIcpQueryDto
from icpquery.captcha import detect_bg_type, fuck_captcha

TEMP_PATH = Path("temp")


async def main():
    async with AsyncIcpQueryDto() as dto:
        await dto.get_token()

        while True:
            captcha = await dto.get_captcha()
            bg_img = cv2.imdecode(np.frombuffer(captcha.bg_img_data, np.uint8), cv2.IMREAD_COLOR)
            bg_type = detect_bg_type(bg_img)
            if bg_type:
                print("detect ok", bg_type)
                print("fucking captcha")
                points = fuck_captcha(captcha)
                if points:
                    print("ok", points)
                else:
                    print("fail")
            else:
                print("detect fail, save temp")
                f = TEMP_PATH / f"{int(time.time()*1000)}.png"
                f.write_bytes(captcha.bg_img_data)
                print(f, "saved")
            await asyncio.sleep(10.0)


asyncio.run(main())

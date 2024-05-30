from itertools import product
from pathlib import Path

import cv2
import numpy as np
from onnxruntime import InferenceSession

from .exceptions import FuckCaptchaFail
from .schema import CaptchaModule, CpatchaBackguard, Points

MODULES_PATH = Path(__file__).parent / "models"
BACKGROUNDS_PATH = Path(__file__).parent / "backgrounds"


def images_mse(img_a: np.ndarray, img_b: np.ndarray) -> float:
    """计算图片相似度"""
    if img_a.shape != img_b.shape:
        raise ValueError

    img_a_gray = cv2.cvtColor(img_a, cv2.COLOR_BGR2GRAY)
    img_b_gray = cv2.cvtColor(img_b, cv2.COLOR_BGR2GRAY)
    h, w = img_a_gray.shape
    diff = cv2.subtract(img_a_gray, img_b_gray)
    err = np.sum(diff**2)
    mse = round(err / (h * w), 2)
    return mse


def detect_backguard(neddle_img: np.ndarray) -> CpatchaBackguard:
    """识别底图"""
    for tag in CpatchaBackguard._member_map_.values():
        hay_file = BACKGROUNDS_PATH / f"{tag.value}.png"
        hay_img = cv2.imread(str(hay_file), cv2.IMREAD_COLOR)
        mse = images_mse(hay_img, neddle_img)
        if mse <= 2.0:
            return tag
    raise FuckCaptchaFail


def mask_backguard(bg_img: np.ndarray, bg_type: CpatchaBackguard) -> np.ndarray:
    """蒙板处理底图"""
    orig_bg_file = BACKGROUNDS_PATH / f"{bg_type.value}.png"
    orig_bg_img = cv2.imread(str(orig_bg_file), cv2.IMREAD_COLOR)

    h, w, _ = bg_img.shape
    new_bg_img = np.zeros(bg_img.shape, dtype=np.uint8)
    for x, y in product(range(h), range(w)):
        if (bg_img[x, y] != orig_bg_img[x, y]).all():
            new_bg_img[x, y] = bg_img[x, y]

    return new_bg_img


def detect_background_object(bg_img: np.ndarray) -> list[tuple]:
    """识别底图文字轮廓外接矩形"""
    bg_img_gray = cv2.cvtColor(bg_img, cv2.COLOR_BGR2GRAY)
    _, bg_img_binary = cv2.threshold(bg_img_gray, 20, 255, cv2.THRESH_BINARY)

    bg_img_binary = cv2.dilate(bg_img_binary, np.ones((4, 4), np.uint8))
    contours, _ = cv2.findContours(
        bg_img_binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )
    boxes = []
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        boxes.append((x, y, w, h))

    return boxes


def detect_answer_point(
    haystack_img: np.ndarray,
    neddle_img: np.ndarray,
    boxes: list[tuple],
    threshold=0.6,
) -> list[tuple]:
    """识别选点坐标"""
    session = InferenceSession(MODULES_PATH / "siamese.onnx")
    positions = [165, 200, 231, 265]
    result_list = []

    for x in positions:
        raw_image2 = neddle_img[11 : 11 + 28, x : x + 26]
        img2 = cv2.cvtColor(raw_image2, cv2.COLOR_BGR2RGB)
        img2 = cv2.resize(img2, (105, 105))
        image_data_2 = img2 / 255.0
        image_data_2 = np.transpose(image_data_2, (2, 0, 1))
        image_data_2 = np.expand_dims(image_data_2, axis=0).astype(np.float32)
        for box in boxes:
            raw_image1 = haystack_img[
                box[1] : box[1] + box[3] + 2, box[0] : box[0] + box[2] + 2
            ]
            img1 = cv2.cvtColor(raw_image1, cv2.COLOR_BGR2RGB)
            img1 = cv2.resize(img1, (105, 105))

            image_data_1 = img1 / 255.0
            image_data_1 = np.transpose(image_data_1, (2, 0, 1))
            image_data_1 = np.expand_dims(image_data_1, axis=0).astype(np.float32)

            inputs = {
                "input": image_data_1,
                "input.53": image_data_2,
            }
            output = session.run(None, inputs)
            output_sigmoid = 1 / (1 + np.exp(-output[0]))
            res = output_sigmoid[0][0]
            if res > threshold:
                result_list.append(box)
    if len(result_list) != 4:
        raise FuckCaptchaFail
    return result_list


def fuck_captcha(captcha: CaptchaModule) -> Points:
    "识别验证码点选位置"
    bg_img = cv2.imdecode(
        np.frombuffer(captcha.get_background_img(), np.uint8), cv2.IMREAD_COLOR
    )
    answer_img = cv2.imdecode(
        np.frombuffer(captcha.get_pointer_img(), np.uint8), cv2.IMREAD_COLOR
    )

    # 识别 减去背景
    bg_type = detect_backguard(bg_img)
    black_bg_img = mask_backguard(bg_img, bg_type)

    # 识别底图对象
    object_boxes = detect_background_object(black_bg_img)

    # 识别相似对象坐标
    answer_points = detect_answer_point(black_bg_img, answer_img, object_boxes)

    points = Points()
    for x, y, w, h in answer_points:
        points.append(
            x=round(x + w / 2),
            y=round(y + h / 2),
        )

    # show
    # bg_h, bg_w, _ = bg_img.shape
    # ans_h, ans_w, _ = answer_img.shape
    # show_img = np.zeros((bg_h + ans_h, bg_w, 3), dtype=np.uint8)
    # show_img[0:ans_h, 0:ans_w, ...] = answer_img
    # show_img[ans_h : bg_h + ans_h, 0:bg_w, ...] = bg_img
    # for object_box in object_boxes:
    #     x, y, w, h = object_box
    #     show_img = cv2.rectangle(
    #         show_img, (x, ans_h + y), (x + w, ans_h + y + h), color=(0, 255, 0)
    #     )
    # positions = [165, 200, 231, 265]
    # for i in range(4):
    #     x = positions[i] + 15
    #     try:
    #         point_x, point_y, point_w, point_h = answer_points[i]
    #     except IndexError:
    #         break
    #     point_x += point_w // 2

    #     show_img = cv2.line(
    #         show_img,
    #         (point_x, ans_h + point_y),
    #         (x, 40),
    #         color=(0, 0, 255),
    #         thickness=2,
    #     )
    # cv2.imshow("bg", show_img)
    # cv2.waitKey()

    return points

from itertools import product
from pathlib import Path

import cv2
import numpy as np
from onnxruntime import InferenceSession

from .exceptions import FuckCaptchaFail
from .schema import CaptchaModule, CpatchaBackguard, Points

# 模型路径
MODULES_PATH = Path(__file__).parent / "models"
# 原始底图路径
BACKGROUNDS_PATH = Path(__file__).parent / "backgrounds"


def images_sim(img_a: np.ndarray, img_b: np.ndarray) -> float:
    """计算图片相似度 使用均方误差(MSE)算法
    Args:
        img_a: 图片A
        img_b: 图片B
    Returns:
        float: 相似度评分(越小越相似)
    """
    if img_a.shape != img_b.shape:
        raise ValueError

    img_a_gray = cv2.cvtColor(img_a, cv2.COLOR_BGR2GRAY)
    img_b_gray = cv2.cvtColor(img_b, cv2.COLOR_BGR2GRAY)
    h, w = img_a_gray.shape
    diff = cv2.subtract(img_a_gray, img_b_gray)
    err = np.sum(diff**2)
    mse = round(err / (h * w), 2)
    return mse


def detect_bg_type(neddle_img: np.ndarray, threshold: float = 2.0) -> CpatchaBackguard:
    """识别底图背景类型
    Args:
        neddle_img: 欲识别的图片
        threshold: 识别阈值
    Returns:
        CpatchaBackguard: 背景图类型
    """
    for tag in CpatchaBackguard._member_map_.values():
        hay_file = BACKGROUNDS_PATH / f"{tag.value}.png"
        hay_img = cv2.imread(str(hay_file), cv2.IMREAD_COLOR)
        mse = images_sim(hay_img, neddle_img)
        if mse <= threshold:
            return tag
    raise FuckCaptchaFail


def remove_bg(orig_img: np.ndarray, bg_type: CpatchaBackguard) -> np.ndarray:
    """去除底图背景
    Args:
        orig_img: 原始图片
        bg_type: 背景类型
    Returns:
        ndarray: 去除背景后的图片
    """
    bg_file = BACKGROUNDS_PATH / f"{bg_type.value}.png"
    bg_img = cv2.imread(str(bg_file), cv2.IMREAD_COLOR)
    new_bg_img = np.zeros_like(orig_img)

    mask = bg_img != orig_img
    new_bg_img[mask] = orig_img[mask]

    return new_bg_img


def detect_obj(bg_img: np.ndarray) -> list[cv2.typing.Rect]:
    """识别底图文字轮廓外接矩形
    Args:
        bg_img: 黑底色带文字的底图
    Returns:
        list[tuple]: 对象区域集 (x, y, w, h)
    """
    bg_img_gray = cv2.cvtColor(bg_img, cv2.COLOR_BGR2GRAY)
    _, bg_img_binary = cv2.threshold(bg_img_gray, 20, 255, cv2.THRESH_BINARY)

    bg_img_binary = cv2.dilate(bg_img_binary, np.ones((4, 4), np.uint8))
    contours, _ = cv2.findContours(bg_img_binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    boxes = [cv2.boundingRect(contour) for contour in contours]

    return boxes


def spilt_pointer_img(pointer_img: np.ndarray) -> list[np.ndarray]:
    """裁剪点选文字图片
    Args:
        pointer_img: 原始文字图片
    Returns:
        list[np.ndarray]: 裁剪后的文字图片列表
    """
    positions = [165, 200, 231, 265]
    imgs = [pointer_img[11 : 11 + 28, x : x + 26] for x in positions]
    return imgs


def detect_answer_pos(
    haystack_img: np.ndarray,
    needle_img_lst: list[np.ndarray],
    roi_boxes: list[cv2.typing.Rect],
    threshold: float = 0.6,
) -> list[tuple]:
    """根据相似度识别文字点选顺序
    Args:
        haystack_img: 底图
        needle_img_lst: 文字图片列表
        boxes: 底图ROI区域列表
        threshold: 识别阈值
    Returns:
        list[tuple]: 符合顺序要求的坐标集列表
    """
    session = InferenceSession(MODULES_PATH / "siamese.onnx")
    result_lst = []

    for needle_img_part in needle_img_lst:
        needle_img_part = cv2.cvtColor(needle_img_part, cv2.COLOR_BGR2RGB)
        needle_img_part = cv2.resize(needle_img_part, (105, 105))
        needle_img_part = needle_img_part / 255.0
        needle_img_part = np.transpose(needle_img_part, (2, 0, 1))
        needle_img_part = np.expand_dims(needle_img_part, axis=0).astype(np.float32)
        for roi_box in roi_boxes:
            x, y, w, h = roi_box
            haystack_img_part = haystack_img[y : y + h + 2, x : x + w + 2]
            haystack_img_part = cv2.cvtColor(haystack_img_part, cv2.COLOR_BGR2RGB)
            haystack_img_part = cv2.resize(haystack_img_part, (105, 105))
            haystack_img_part = haystack_img_part / 255.0
            haystack_img_part = np.transpose(haystack_img_part, (2, 0, 1))
            haystack_img_part = np.expand_dims(haystack_img_part, axis=0).astype(np.float32)

            inputs = {
                "input": haystack_img_part,
                "input.53": needle_img_part,
            }
            output = session.run(None, inputs)
            output_sigmoid = 1 / (1 + np.exp(-output[0]))
            res = output_sigmoid[0][0]
            if res > threshold:
                result_lst.append(
                    (
                        round(x + w / 2),  # X
                        round(y + h / 2),  # Y
                    )
                )
    if len(result_lst) != 4:
        raise FuckCaptchaFail
    return result_lst


def fuck_captcha(captcha: CaptchaModule) -> Points:
    "识别验证码点选位置"
    orig_bg_img = cv2.imdecode(np.frombuffer(captcha.get_bg_img(), np.uint8), cv2.IMREAD_COLOR)
    orig_ptr_img = cv2.imdecode(np.frombuffer(captcha.get_ptr_img(), np.uint8), cv2.IMREAD_COLOR)

    # 切分点选文字图片
    pointer_img_lst = spilt_pointer_img(orig_ptr_img)

    # 识别并去除底图背景
    bg_type = detect_bg_type(orig_bg_img)
    plain_bg_img = remove_bg(orig_bg_img, bg_type)

    # 识别底图对象
    roi_boxes = detect_obj(plain_bg_img)

    # 识别相似对象坐标
    answer_points = detect_answer_pos(plain_bg_img, pointer_img_lst, roi_boxes)

    # 序列化坐标
    points = Points.from_list(answer_points)

    # # DEBUG
    # bg_h, bg_w, _ = orig_bg_img.shape
    # ans_h, ans_w, _ = orig_ptr_img.shape
    # show_img = np.zeros((bg_h + ans_h, bg_w, 3), dtype=np.uint8)
    # show_img[0:ans_h, 0:ans_w, ...] = orig_ptr_img
    # show_img[ans_h : bg_h + ans_h, 0:bg_w, ...] = orig_bg_img
    # for roi_box in roi_boxes:
    #     x, y, w, h = roi_box
    #     show_img = cv2.rectangle(
    #         show_img,
    #         (x, ans_h + y),
    #         (x + w, ans_h + y + h),
    #         color=(0, 255, 0),
    #     )
    # positions = [165, 200, 231, 265]
    # for i in range(4):
    #     x = positions[i] + 15
    #     try:
    #         point_x, point_y = answer_points[i]
    #     except IndexError:
    #         break

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

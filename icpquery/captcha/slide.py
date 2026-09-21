import cv2
import numpy as np

from ..schema.captcha import CaptchaSlideModule


def find_consecutive_runs(arr: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """查找数组连续区间
    Args:
        arr: 目标数组
    Returns:
        np.ndarray: 区间起始位置列表
        np.ndarray: 区间长度列表
    """
    arr_len = len(arr)
    run_start = np.zeros(arr_len, dtype=bool)
    run_start[0] = True
    run_start[1:] = ~np.isclose(arr[1:], arr[:-1])

    run_starts = np.nonzero(run_start)[0]
    run_lengths = np.diff(np.append(run_starts, arr_len))

    return run_starts[run_lengths > 1], run_lengths[run_lengths > 1]


def detect_answer_pos(target_img: np.ndarray, box_min_threshold: int = 66) -> int | None:
    """识别条带滑块位置
    Args:
        target_img: 目标图片
        box_min_threshold: 滑块最小宽度阈值
    Returns:
        int | None: 滑块x坐标
    """
    _, img_w = target_img.shape[:2]

    # 按列计算BGR像素方差
    col_variance = np.array([np.var(target_img[:, x]) for x in range(img_w)])

    starts, lens = find_consecutive_runs(col_variance)

    # 寻找滑块区间起始位置
    for start, len in zip(starts, lens):
        if len >= box_min_threshold:
            return int(start)
    return None


def crop_bgimg_tile(bg_img: np.ndarray, y_offset: int) -> np.ndarray:
    return bg_img[y_offset : y_offset + 66]


def debug_answer_slide(bg_img: np.ndarray, sllider_y_pos: int, slider_x_pos: int):
    bg_h, bg_w, _ = bg_img.shape
    show_img = np.zeros((bg_h, bg_w, 3), dtype=np.uint8)
    show_img[0:bg_h, 0:bg_w, ...] = bg_img
    cv2.rectangle(show_img, (0, sllider_y_pos), (bg_w, sllider_y_pos + 66 + 1), (0, 255, 0), 2)
    cv2.rectangle(
        show_img,
        (slider_x_pos, sllider_y_pos),
        (slider_x_pos + 66 + 1, sllider_y_pos + 66 + 1),
        (0, 0, 255),
        2,
    )

    cv2.imshow("answer_slide", show_img)


def fuck_slide_captcha(captcha: CaptchaSlideModule) -> int | None:
    """识别验证码滑块位置
    Args:
        captcha: 滑动验证码数据
    Returns:
        int | None: 滑块x位置
    """
    bg_img = cv2.imdecode(np.frombuffer(captcha.bg_img_data, np.uint8), cv2.IMREAD_COLOR)
    if bg_img is None:
        return None

    # 裁切目标底图条带
    bg_tile_img = crop_bgimg_tile(bg_img, captcha.height + 1)

    # 识别滑块位置
    x_pos = detect_answer_pos(bg_tile_img)
    if x_pos is None:
        return None

    # DEBUG
    # debug_answer_slide(bg_img, captcha.height + 1, x_pos)
    # cv2.waitKey()

    return x_pos

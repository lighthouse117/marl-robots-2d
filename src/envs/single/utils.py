from typing import Tuple


def line_intersect(p0, p1, q0, q1) -> Tuple[float, float]:
    """
    2つの直線PとQの交点を計算
    pからp+rに向かう直線とqからq+sに向かう直線が
    p+trおよびq+usで交わるようなtとuを求める
    """
    det = (p1[0] - p0[0]) * (q1[1] - q0[1]) + (p1[1] - p0[1]) * (q0[0] - q1[0])
    if det != 0:
        t = (
            (q0[0] - p0[0]) * (q1[1] - q0[1]) + (q0[1] - p0[1]) * (q0[0] - q1[0])
        ) / det
        u = (
            (q0[0] - p0[0]) * (p1[1] - p0[1]) + (q0[1] - p0[1]) * (p0[0] - p1[0])
        ) / det
        if 0 <= t <= 1 and 0 <= u <= 1:
            return (p0[0] + t * (p1[0] - p0[0]), p0[1] + t * (p1[1] - p0[1]))
    return None

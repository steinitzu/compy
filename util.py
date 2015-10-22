import math

def distance(pointa, pointb):
    """
    _distance((x,y), (x, y)) -> float
    Get the distance between two points.
    """
    return math.sqrt(
        (pointa[0]-pointb[0])**2
        + (pointa[1]-pointb[1])**2)

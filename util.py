import math
import collections
import heapq


def distance(pointa, pointb):
    """
    _distance((x,y), (x, y)) -> float
    Get the distance between two points.
    """
    return math.sqrt(
        (pointa[0]-pointb[0])**2
        + (pointa[1]-pointb[1])**2)


class Queue:
    def __init__(self):
        self.elements = collections.deque()

    def empty(self):
        return len(self.elements) == 0

    def put(self, x):
        self.elements.append(x)

    def get(self):
        return self.elements.popleft()


class PriorityQueue:
    def __init__(self):
        self.elements = []

    def empty(self):
        return len(self.elements) == 0

    def put(self, item, priority):
        heapq.heappush(self.elements, (priority, item))

    def get(self):
        return heapq.heappop(self.elements)[1]

from component import *

"""
Experimenting with collision manager using Spatial component.
"""

class CollisionManager(object):

    def __init__(self, *entities):
        self.add(*entities)
        self.known_entities = set()

    def add(self, *entities):
        for e in entities:
            if isinstance(e, Component):
                e = e.entity
            self.known_entities.add(e)

    def remove(self, entity):
        self.known_entities.remove(entity)

    def is_known(self, entity):
        return entity in self.known_entities

    def objs_colliding(self, entity):
        e = entity.component(Spatial)
        for other in self.known_entities:
            o = other.component(Spatial)
            if e.left >= o.right or e.right <= o.left:
                continue
            if e.bottom >= o.top or e.top <= o.bottom:
                continue
            yield other.component(Collisions)

    def known_objs(self):
        return self.known_entities

    def clear(self):
        self.known_entities.clear()

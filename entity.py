import types
from collections import OrderedDict

from cocos.sprite import Sprite
from cocos.rect import Rect
from cocos import collision_model

from component import *


class Entity(object):
    def __init__(self, *components):
        self.components = OrderedDict()
        self.add_components(*components)

    def add_components(self, *components):
        for component in components:
            component.entity = self
            self.components[component.add_as] = component
            component.on_add()

    def component(self, klass):
        return self.components[klass]

    def remove_component(self, component):
        if isinstance(component, types.ClassType):
            self.components.pop(component)
        else:
            self.components.pop(component.__class__)

    def kill(self):
        self.systems_manager.remove(self)


class Player(Entity):
    def __init__(self, *args, **kwargs):
        super(self.__class__, self).__init__(*args, **kwargs)
        self.add_component(Movement())
        self.add_component(Collisions())
        self.add_component(Health())
        self.add_components(Team('Humans'))


class Platform(Entity):
    pass


class Obstacle(Entity):
    pass


class AIPlayer(Entity):
    pass

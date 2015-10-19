import types
from collections import OrderedDict

from cocos.sprite import Sprite
from cocos.rect import Rect
from cocos import collision_model

from component import *


class BoundRect(Rect):

    """
    A Rect object that updates sprite position
    accordingly on any position changes.
    Also updates Sprite's cshape (if present)
    """

    def __init__(self, *args, **kwargs):
        self.sprite = kwargs.pop('sprite')
        super(BoundRect, self).__init__(*args, **kwargs)
        # Old rect, holds position of object before movement
        self.old = Rect(self.x, self.y, self.width, self.height)

    def _set_property(self, name, value):
        # Set value of old to current value
        setattr(self.old, name, getattr(self, name))
        object.__setattr__(self, name, value)
        self.sprite.position = self.center
        try:
            self.sprite.cshape.center = self.sprite.position
        except:
            # Object doesn't have a cshape, carry on
            pass

    def __setattr__(self, name, value):
        posattrs = ('bottom', 'top', 'left', 'right',
                    'center', 'midtop', 'midbottom',
                    'midleft', 'midright', 'topleft', 'topright',
                    'bottomleft', 'bottomright',
                    'x', 'y')
        if name in posattrs:
            self._set_property(name, value)
        else:
            object.__setattr__(self, name, value)


class Entity(Sprite):
    """
    A sprite that has a square cshape attribute and
    a BoundRect as a .rect attr.
    The rect is aligned with the collision shape.
    """

    def __init__(self, image, width_multi=0.9, height_multi=0.9):
        super(self.__class__, self).__init__(image)
        # self.cshape = collision_model.CircleShape(self.position,
        #                                           self.height/2)
        box_width = int(self.width*width_multi)
        box_height = int(self.height*height_multi)
        self.cshape = collision_model.AARectShape(self.position,
                                                  box_width/2,
                                                  box_height/2)
        self.schedule(self.update)

        self.rect = self.get_rect()
        self.rect.width = int(self.width*width_multi)
        self.rect.height = int(self.height*height_multi)

        self.components = OrderedDict()

    def add_components(self, *components):
        for component in components:
            component.entity = self
            self.components[component.add_as] = component
            component.on_add()

    def remove_component(self, component):
        if isinstance(component, types.ClassType):
            self.components.pop(component)
        else:
            self.components.pop(component.__class__)

    def component(self, klass):
        """
        Get component for given klass.
        """
        return self.components[klass]

    def update(self, dt, *args, **kwargs):
        pass

    def get_rect(self):
        """
        Overriden to return a BoundRect insted of cocos.rect.Rect
        """
        x, y = self.position
        x -= self.image_anchor_x
        y -= self.image_anchor_y
        return BoundRect(x, y, self.width, self.height, sprite=self)


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

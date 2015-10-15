import types

from cocos.sprite import Sprite
from cocos.rect import Rect


class BoundRect(Rect):

    """
    A Rect object that updates sprite position
    accordingly on any position changes.
    Also updates Sprite's cshape (if present)
    """

    def __init__(self, *args, **kwargs):
        self.sprite = kwargs.pop('sprite')
        super(BoundRect, self).__init__(*args, **kwargs)

    def _set_property(self, name, value):
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
        super(CollidableSprite, self).__init__(image)
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

        self.components = {}

    def add_component(self, component):
        component.entity = self
        self.components[component.__class__] = component

    def remove_component(self, component):
        if isinstance(component, types.ClassType):
            self.components.pop(component)
        else:
            self.components.pop(component.__class__)

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
    pass


class Platform(Entity):
    pass


class Obstacle(Entity):
    pass


class AIPlayer(Entity):
    pass

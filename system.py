from component import *


class System(object):
    pass


class MovementSystem(System):
    def __init__(self, *components):
        self.movement = None
        self.collisions = None
        self.gravity = None
        for c in components:
            if isinstance(c, Movement):
                self.movement = c
            elif isinstance(c, Collisions):
                self.collisions = c
            elif isinstance(c, Gravity):
                self.gravity = c
        if not self.movement:
            raise Exception('MovementSystem must be initialized'
                            + ' with at least a'
                            + ' components.Movement component.')

    def _move_horizontal(self, entity, movement, dt):
        vx = movement.velocity[0]
        entity.rect.x += vx * dt
        if self.collisions:
            for ob in self.collisions.get_colliding():
                # Check and correct position if entity collides
                # with a solid edge
                if vx > 0:
                    if 'left' not in ob.components[Collissions].solid_edges:
                        continue
                    entity.rect.right = ob.rect.left
                    movement.velocity[0] = 0
                    movement.acceleration[0] = 0
                elif vx < 0:
                    if 'right' not in ob.components[Collissions].solid_edges:
                        continue
                    entity.rect.left = ob.rect.right
                    movement.velocity[0] = 0
                    movement.acceleration[0] = 0

    def _move_vertical(self, entity, movement, dt):
        vy = movement.velocity[1]
        try:
            vy -= self.gravity.amount
        except AttributeError:
            # No gravity
            pass
        old_bottom = entity.rect.bottom
        entity.rect.y += vy * dt
        if self.collisions:
            for ob in self.collisions.get_colliding():
                if vy > 0:
                    # moving up
                    if 'bottom' not in ob.components[Collissions].solid_edges:
                        continue
                    entity.rect.top = ob.rect.bottom
                    movement.velocity[1] = 0
                    movement.acceleration[1] = 0
                elif vy < 0:
                    if 'top' not in ob.components[Collissions].solid_edges:
                        continue
                    if old_bottom < ob.rect.top:
                        continue
                    entity.rect.bottom = ob.rect.top
                    movement.velocity[1] = 0
                    movement.acceleration[1] = 0

    def move(self, dt):
        entity = self.movement.entity
        movement = self.movement
        self.move_horizontal(entity, movement, dt)
        self.move_vertical(entity, movement, dt)

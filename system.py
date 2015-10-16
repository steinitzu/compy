from component import *
from entity import Entity


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
        self.collision_handlers = []
        c = self.collisions
        if c:
            for h in c.collision_handlers:
                if h == c.CORRECT_POSITION:
                    self.collision_handlers.append(
                        self._correct_position_handler)
                elif h == c.DAMAGE:
                    self.collision_handlers.append(self._damage_handler)
                elif h == c.PUSH:
                    self.collision_handlers.append(self._push_handler)

    def _move_horizontal(self, entity, movement, dt):
        vx = movement.velocity[0]
        entity.rect.x += vx * dt
        if self.collisions:
            for ob in self.collisions.get_colliding():
                for h in self.collision_handlers:
                    h(entity, ob, axis='x')

    def _move_vertical(self, entity, movement, dt):
        vy = movement.velocity[1]
        try:
            vy -= self.gravity.amount
        except AttributeError:
            # No gravity
            pass
        entity.rect.y += vy * dt
        if self.collisions:
            for ob in self.collisions.get_colliding():
                for h in self.collision_handlers:
                    h(entity, ob, axis='y')

    def move(self, dt):
        entity = self.movement.entity
        movement = self.movement
        self.move_horizontal(entity, movement, dt)
        self.move_vertical(entity, movement, dt)


class ColliisionSystem(self):
    def __init__(self, entity):
        super(self.__class__, self).__init__()
        self.entity = entity
        if Collisions not in entity.components:
            raise Exception('Entity must have a Collisions component')
        handlers = []
        if Hurt in entity.components:
            handlers.append(self.deal_damage)
        if Push in entity.components:
            handlers.append(self.push)
        if (Movement in entity.components
            and (Push not in entity.components
                 and Hurt not in entity.components)):
            handlers.append(self.correct_position)
        self.handlers = handlers

    def correct_position(self, entity, colliding_object, axis='x'):
        """
        This handler is for moving entities.
        When entity collides with object, it's position will be corrected
        so that it is no longer colliding.
        """
        solid_edges = colliding_object.component[Collisions].solid_edges
        movement = entity.component(Movement)
        # Axis can be X or Y
        if axis == 'x':
            if movement.velocity[0] > 0:
                if 'left' not in solid_edges:
                    return
                entity.rect.right = colliding_object.rect.left
            elif movement.velocity[0] < 0:
                if 'right' not in solid_edges:
                    return
                entity.rect.left = colliding_object.rect.right
            movement.velocity[0] = 0
            movement.acceleration[0] = 0
        elif axis == 'y':
            if movement.velocity[1] > 0:
                # Moving up
                if 'bottom' not in solid_edges:
                    return
                entity.rect.top = colliding_object.rect.bottom
            elif movement.velocity[1] < 0:
                if 'top' not in solid_edges:
                    return
                if entity.rect.old.bottom < colliding_object.rect.top:
                    return
                entity.rect.bottom = colliding_object.rect.top
            movement.velocity[1] = 0
            movement.acceleration[1] = 0

    def deal_damage(self, entity, colliding_object, axis=None):
        """
        This handler deals damage to colliding object.
        This is for entities with a Hurt component (e.g. a bullet)
        """
        base_damage = entity.components[Attack].damage
        try:
            if (entity.component(Team) != colliding_object.component(Team)
                or config.TEAMKILL):
                colliding_object.health.take_damage(base_damage)
        except KeyError:
            return

    def push(self, entity, colliding_object, axis=None):
        """
        This handler pushes colliding object back.
        This is for entities with a Push component. (e.g. a sonic attack)
        """
        # Axis doesn't matter here
        strength = entity.component(Push).strength
        v = entity.component(Movement).velocity
        try:
            colliding_object.component(Movement).velocity = [
                v[0]*strength, v[1]*strength]
        except KeyError:
            # Colliding object is not movable, carry on
            pass


class AttackSystem(System):

    def __init__(self, fast=None, strong=None, ranged=None):
        self.fast = fast
        self.strong = strong
        self.ranged = ranged

    def build_ranged_attack(self):
        if not self.ranged:
            return
        p = self.ranged.entity
        e = Entity()
        e.add_component(self.ranged)
        e.add_component(Movement())
        if self.ranged.push:
            e.add_component(Push(strength=self.ranged.push))
        try:
            e.add_component(p.components[Team])
        except KeyError:
            pass
        # TODO: calculate velocity based on angle
        e.components[Movement].velocity = [self.ranged.travel_velocity, 0]
        # Attach a movement system and add to world in caller
        return e

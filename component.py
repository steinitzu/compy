import config


class Component(object):

    def __init__(self):
        self.entity = None

    def update(self, dt):
        # Called each frame
        pass


class Display(Component):
    def __init__(self, images):
        super(Health, self).__init__()
        self.images = images


class Health(Component):
    def __init__(self):
        super(Health, self).__init__()
        self.amount = 100

    def is_dead(self):
        return self.amount <= 0

    def take_damage(self, damage):
        self.amount -= damage


class Team(Component):
    def __init__(self):
        super(self.__class__, self).__init__()
        self.name = '0'

    def __eq__(self, other):
        return self.name == other.name

    def __ne__(self, other):
        return self.name != other.name


class Hurt(Component):
    def __init__(self, damage=10):
        super(self.__class__, self).__init__()
        self.damage = damage


# Attack should be an entity with Push, Hurt and Team components
# Not a component
# class Attack(Component):
#     def __init__(self):
#         super(self.__class__, self).__init__()
#         self.damage = 10
#         # Range is 0 for melee attacks
#         self.range = 0
#         # Travel Speed is 0 for melee attacks
#         self.travel_velocity = 0
#         # Push value. Multiplied by travel velocity.
#         self.push = 1


class Push(Component):
    """
    This component, coupled with a push component
    will push any entity it comes into contact with.
    """
    def __init__(self, strength=1):
        super(self.__class__, self).__init__()
        self.strength = strength


class Movement(Component):
    def __init__(self):
        super(self.__class__, self).__init__()
        self.acceleration = [0, 0]
        self.velocity = [0, 0]
        self.walk_acceleration = 10*config.METER
        self.max_walk_speed = 10*config.METER
        self.jump_velocity = 10*config.METER

    def walk(self, accel_mod):
        if self.max_walk_speed and abs(self.velocity[0]) < self.max_walk_speed:
            self.acceleration[0] = self.walk_acceleration*accel_mod
        else:
            self.acceleration[0] = 0

    def jump(self):
        self.velocity[1] = self.jump_velocity

    def end_jump(self):
        self.velocity[1] = 0

    def update(self, dt):
        # Update velocity using acceleration, call each frame
        self.velocity[0] += self.acceleration[0]*dt
        self.velocity[1] += self.acceleration[1]*dt


class Collisions(Component):
    def __init__(self, collidables):
        super(self.__class__, self).__init__()
        # collidables should be a CollisionManager instance
        self.collidables = collidables
        self.solid_edges = ['left', 'right', 'top', 'bottom']

    def get_colliding(self):
        return self.colliding.objs_colliding(self.entity)


class Gravity(Component):
    """
    Add this to Entity to make it fall by config.GRAVITY every second.
    Must have a Movement component as well.
    """
    def __init__(self):
        super(self.__class__, self).__init__()
        self.amount = config.GRAVITY*0.5

    def update(self, dt):
        # Gravity amount updated every frame gravity*time
        self.amount = config.GRAVITY*dt

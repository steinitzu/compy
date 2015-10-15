import config


class Component(object):

    def __init__(self):
        self.entity = None

    def update(self, dt):
        # Called each frame
        pass


class Health(Component):
    def __init__(self):
        super(Health, self).__init__()
        self.amount = 100

    def is_dead(self):
        return self.amount <= 0

    def take_damage(self, damage):
        self.amount -= damage


class Attack(Component):
    def __init__(self):
        super(self.__class__, self).__init__()


class Movement(Component):
    def __init__(self):
        super(self.__class__, self).__init__()
        self.acceleration = [0, 0]
        self.velocity = [0, 0]

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
    def __init__(self):
        super(self.__class__, self).__init__()
        self.amount = config.GRAVITY*0.5

    def update(self, dt):
        # Gravity amount updated every frame gravity*time
        self.amount = config.GRAVITY*dt

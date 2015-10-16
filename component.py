import config


class Component(object):

    def __init__(self):
        self.entity = None
        # Added with this classname
        self.add_as = self.__class__

    def on_add(self):
        """
        Called when component is added to entity.
        """
        pass

    def update(self, dt):
        # Called each frame
        pass


class Display(Component):
    def __init__(self, images):
        """
        images should be a dict of pyglet images, or paths.
        {name: Image}
        """
        super(self.__class__, self).__init__()
        self.images = images

    def set_image(self, name):
        self.entity.image = self.images[name]


class Health(Component):
    def __init__(self):
        super(Health, self).__init__()
        self.amount = 100

    def is_dead(self):
        return self.amount <= 0

    def take_damage(self, damage):
        self.amount -= damage


class Team(Component):
    def __init__(self, name):
        super(self.__class__, self).__init__()
        self.name = name

    def __eq__(self, other):
        return self.name == other.name

    def __ne__(self, other):
        return self.name != other.name


class Hurt(Component):
    def __init__(self, damage=10):
        super(self.__class__, self).__init__()
        self.damage = damage


class Weapon(Component):
    # When a player changes weapons, just swap out his Weapon component
    # Keep a second list of components not equipped
    def __init__(self):
        super(self.__class__, self).__init__()

    def get_components(self):
        """
        Return a list of components
        which will be used to create an attack entity.
        Override this method in subclass.
        """
        team = self.entity.components.get(Team, None)
        teamname = team.name if team else ''
        return [Team(teamname)]


class Fist(Weapon):
    def __init__(self, damage=10):
        super(self.__class__, self).__init__()
        self.add_as = Weapon
        self.damage = damage

    def get_components(self):
        base = super(self.__class__, self).get_components()

        return [Hurt(self.damage),
                Push(),
                Collisions()] + base


class Pistol(Weapon):
    def __init__(self, damage=10):
        super(self.__class__, self).__init__()
        self.add_as = Weapon
        self.damage = damage
        # When a bullet goes off screen, delete it

    def get_components(self):
        # Get the components for a bullet
        base = super(self.__class__, self).__init__()
        return [Hurt(self.damage),
                Collisions(),
                Movement()] + base


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
        self.max_walk_speed = 6*config.METER
        self.jump_acceleration = 20*config.METER
        self.max_jump_speed = 5*config.METER
        self.is_jumping = False

    def walk(self, accel_mod):
        if self.max_walk_speed and abs(self.velocity[0]) < self.max_walk_speed:
            self.acceleration[0] = self.walk_acceleration*accel_mod
        else:
            self.acceleration[0] = 0

    def end_walk(self):
        self.velocity[0] = 0
        self.acceleration[0] = 0

    def jump(self):
        if not self.is_jumping and self.velocity[1] == 0:
            self.is_jumping = True
            self.acceleration[1] = self.jump_acceleration

    def end_jump(self):
        if self.is_jumping:
            self.is_jumping = False
            self.acceleration[1] = 0

    def update(self, dt):
        # Update velocity using acceleration, call each frame
        self.velocity[0] += self.acceleration[0]*dt
        if self.velocity[1] >= self.max_jump_speed:
            # To prevent jumping to infinite heights
            self.acceleration[1] = 0
        self.velocity[1] += self.acceleration[1]*dt


class Collisions(Component):
    def __init__(self, collidables):
        super(self.__class__, self).__init__()
        # collidables should be a CollisionManager instance
        # Parent entity is added to collision manager when
        # this component is added to entity
        self.collidables = collidables
        self.solid_edges = ['left', 'right', 'top', 'bottom']

    def get_colliding(self):
        return self.collidables.objs_colliding(self.entity)

    def on_add(self):
        self.collidables.add(self.entity)


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

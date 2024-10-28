import pygame as pg
import random

LENGTH_TOL = 0.01  # for handling lerp with velocity magnitude ~ 0.
ANGLE_TOL = 0.1  # for handling slerp with angles ~ 180 degrees.


class Fish:
    def __init__(self, position):
        # == Constants ==
        # Body Parts
        self.BODY_SIZES = [68, 79, 82, 83, 75, 71, 68, 64, 57, 43, 34, 32, 19, 16]
        self.DORSEL_FINS = [
            pg.Vector2(-60, 0),
            pg.Vector2(-40, -45),
            pg.Vector2(-20, -60),
            pg.Vector2(0, -70),
            pg.Vector2(15, -75),
            pg.Vector2(20, -73),
            pg.Vector2(25, -60),
            pg.Vector2(28, -45),
            pg.Vector2(10, -20),
            pg.Vector2(0, 0),
            pg.Vector2(10, 20),
            pg.Vector2(28, 45),
            pg.Vector2(25, 60),
            pg.Vector2(20, 73),
            pg.Vector2(15, 75),
            pg.Vector2(0, 70),
            pg.Vector2(-20, 60),
            pg.Vector2(-40, 45)
        ]
        self.ANAL_FINS = [
            pg.Vector2(-40, 0),
            pg.Vector2(10, -40),
            pg.Vector2(15, -30),
            pg.Vector2(0, 0),
            pg.Vector2(15, 30),
            pg.Vector2(10, 40)
        ]
        self.VERTABRAE_LENGTH = 30

        self.COLOR = pg.Color(50,116,154,255)
        self.LCOLOR = self.COLOR.lerp(pg.Color("white"), 0.2)

        # movement paramaters
        self.MAX_ROTATION = 30
        self.ACCELERATION = 0.1
        self.SCARED_SPEED = 4
        self.IDLE_SPEED = 0.5
        self.HUNT_SPEED = 2
        self.PLAYER_SPEED = 1.8
        self.FAST_PLAYER_SPEED = 4
        self.SLOW_PLAYER_SPEED = 1

        # behaviour
        self.SCARED_TIME = 2

        # == Variables ==
        # body structure
        self.nodes = []
        self.generate_body(position) # initialize body parts
        self.vecs = []

        # movement variables
        self.target_vel = pg.Vector2(0.1, 0.1)
        self.vel = (self.nodes[0] - self.nodes[1]).normalize()

        # behaviour
        self.scare_timer = 0
        self.go_idle()

        # environment
        self.world = []
    
    @property
    def head_pos(self):
        '''Easy way to access head node.'''
        return self.nodes[0]

    @property
    def outline(self):
        '''Outline of main body.'''
        sides = []
        for vec, node, b in zip(self.vecs, self.nodes, self.BODY_SIZES):
            lhs = node + vec.rotate(90).normalize() * b / 2
            sides.append(lhs)
        # tailbone
        sides.append(node + vec.normalize() * b / 2)
        rsides = []
        for vec, node, b in zip(self.vecs, self.nodes, self.BODY_SIZES):
            rhs = node + vec.rotate(-90).normalize() * b / 2
            rsides.append(rhs)
        rsides = list(reversed(rsides))
        sides.extend(rsides)
        # head
        h, v, b = self.head_pos, self.vecs[0], self.BODY_SIZES[0]
        h1 = h + v.rotate(225).normalize() * b / 2
        h2 = h + v.rotate(180).normalize() * b / 2 
        h3 = h + v.rotate(135).normalize() * b / 2 
        sides.extend([h1, h2, h3])

        return sides

    def set_color(self, color):
        '''Set color of fish and its secondary as a slightly lighter shade.'''
        self.COLOR = color
        self.LCOLOR = self.COLOR.lerp(pg.Color("white"), 0.2)

    @property
    def eyes(self):
        '''Get eye locations from head position and direction facing.'''
        h, v, b = self.head_pos, self.vecs[0], self.BODY_SIZES[0]
        e1 = h + v.rotate(105).normalize() * b / 2 * 0.7
        e2 = h + v.rotate(245).normalize() * b / 2 * 0.7

        return e1, e2

    def generate_body(self, position):
        '''Adds variety to how fish spawns in direction wise.'''
        # get random starting angle and add body parts
        p0 = pg.Vector2(position)
        vec = pg.Vector2.from_polar((self.VERTABRAE_LENGTH, random.randint(0, 360)))
        for body in range(len(self.BODY_SIZES)):
            self.nodes.append(p0 + body * vec)

    def update(self):
        '''Main update function to be called in game loop.'''
        # behaviour
        if self.scare_timer > 0:
            self.scare_timer -= 1/60
            if self.scare_timer <= 0:
                self.scare_timer = 0
                self.go_idle()
        
        # movement
        if 180 + ANGLE_TOL > self.vel.angle_to(self.target_vel) > 180 - ANGLE_TOL:
            self.vel.rotate(1)
        else:
            if self.vel.length() < LENGTH_TOL or self.target_vel.length() < LENGTH_TOL:
                self.vel = self.vel.lerp(self.target_vel, self.ACCELERATION)
            else:
                self.vel = self.vel.slerp(self.target_vel, self.ACCELERATION)
        self.nodes[0] += self.vel

        self.update_body()
    
    def update_body(self):
        '''Procedural animation for body movement.'''
        self.vecs = []
        vecp = None
        vec = None
        for i, node in enumerate(self.nodes):
            if i != 0:
                vec = (node - self.nodes[i-1]).normalize() * self.VERTABRAE_LENGTH
                if vecp:
                    ang_to = vec.angle_to(vecp)
                    if ang_to > 180:
                        ang_to -= 360
                    if ang_to < -180:
                        ang_to += 360
                    if abs(ang_to) > self.MAX_ROTATION:
                        target = vecp.rotate(ang_to / abs(ang_to) * -self.MAX_ROTATION)
                        snap = pg.math.clamp(0.1 + 0.9 * (abs(ang_to) - self.MAX_ROTATION) ** 1.3 / 80, 0, 1) # the more angled the body is the more it wants to straighten out.
                        vec = vec.slerp(target, snap)

                self.nodes[i] = (self.nodes[i-1] + vec)
                vecp = vec
                self.vecs.append(vec)
        if vec:
            self.vecs.append(vec)
    
    def go_idle(self):
        target_pos = pg.Vector2.from_polar((1, random.randint(0, 360)))
        self.target_vel = target_pos * self.IDLE_SPEED
        
    def hunt_food(self, location):
        self.target_vel = (location - self.head_pos).normalize() * self.HUNT_SPEED

    def frighten(self, location):
        self.target_vel = (self.head_pos - location).normalize() * self.SCARED_SPEED
        self.scare_timer = self.SCARED_TIME

    def render(self, surface, camera_pos):
        sides = [camera_pos + s for s in self.outline]
        e1, e2 = self.eyes

        # fins
        # pectoral
        angle = self.vecs[2].as_polar()[1]
        points = [camera_pos + self.nodes[3] + dpoint.rotate(angle) for dpoint in self.DORSEL_FINS]
        pg.draw.polygon(surface, self.LCOLOR, points)
        pg.draw.lines(surface, pg.Color(255, 255, 255), True, points, 4)

        # anal
        angle = self.vecs[9].as_polar()[1]
        points = [camera_pos + self.nodes[10] + dpoint.rotate(angle) for dpoint in self.ANAL_FINS]
        pg.draw.polygon(surface, self.LCOLOR, points)
        pg.draw.lines(surface, pg.Color(255, 255, 255), True, points, 4)

        pg.draw.polygon(surface, self.COLOR, sides)
        pg.draw.lines(surface, pg.Color(255, 255, 255), True, sides, 4)
        pg.draw.circle(surface, pg.Color(255, 255, 255), e1 + camera_pos, 5)
        pg.draw.circle(surface, pg.Color(255, 255, 255), e2 + camera_pos, 5)


if __name__ == "__main__":
    RESOLUTION = WIDTH, HEIGHT = 1920, 1080
    FPS = 60
    BG_COLOR = pg.Color(59, 75, 69)

    screen = pg.display.set_mode(RESOLUTION)
    clock = pg.time.Clock()

    fish = Fish((WIDTH // 2, HEIGHT // 2))
    camera = pg.Vector2()

    running = True
    while running:
        dt = clock.tick(FPS)
        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False
            if event.type == pg.MOUSEBUTTONDOWN:
                if event.button == 1:
                    fish.hunt_food(event.pos)
                if event.button == 3:
                    fish.frighten(event.pos)
        
        # update
        fish.update()

        # render
        screen.fill(BG_COLOR)
        fish.render(screen, camera)
        pg.display.flip()
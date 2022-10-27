import math
import os
import pickle
import random

import neat
import pygame

pygame.font.init()

WIN_WIDTH, WIN_HEIGHT = 400, 600
WIN = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
pygame.display.set_caption("Space Invader")

WHITE = (255, 255, 255)
BULLET_COLOR = (255, 255, 0)
FPS = 60
SCORE_FONT = pygame.font.SysFont('comicsans', 30)
DEL_ASTEROID = pygame.USEREVENT + 1

SPACESHIP_HEIGHT = 50
SPACESHIP_WIDTH = 69

SPACESHIP_IMG = pygame.image.load(os.path.join('Assets', 'spaceship.png'))
SPACESHIP_IMG = pygame.transform.scale(SPACESHIP_IMG, (SPACESHIP_WIDTH, SPACESHIP_HEIGHT))
SPACESHIP_IMG = pygame.transform.rotate(SPACESHIP_IMG, 180)

EXPLOSION_IMG = pygame.transform.scale(pygame.image.load(os.path.join('Assets', 'explosion.png')),
                                       (SPACESHIP_WIDTH, SPACESHIP_HEIGHT))
BACKGROUND_IMG = pygame.image.load(os.path.join('Assets', 'space.png'))


class Spaceship:
    SPACESHIP_VELOCITY = 5
    IMG = SPACESHIP_IMG

    BULLET_VELOCITY = 5
    BULLET_HEIGHT, BULLET_WIDTH = 10, 5
    MAX_BULLETS = 3

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = SPACESHIP_WIDTH
        self.height = SPACESHIP_HEIGHT
        self.bullets = []
        self.tick = 0
        self.score = 0
        self.available_asteroids = []

    def move_right(self):
        """
        moves the spaceship right as long as its right side does not go out of the screen
        :return: None
        """
        if self.x + self.SPACESHIP_VELOCITY + self.width < WIN_WIDTH:
            self.x += self.SPACESHIP_VELOCITY
            asteroid = self.available_asteroids[0]
            '''x = asteroid.x + math.tan(asteroid.angle) * (self.y - asteroid.y)
            if self.x - self.SPACESHIP_VELOCITY < x:
                return 0.1 - (abs(self.x - x)) / 4000
            else:
                return -(0.1 - (abs(self.x - x)) / 4000)'''
            x = asteroid.rect.center[0] + (
                    (self.y - asteroid.rect.center[1]) / (1 + math.cos(asteroid.angle))) * math.sin(asteroid.angle)
            # x = asteroid.rect.center[0]
            if self.x - self.SPACESHIP_VELOCITY <= x:
                return 0.1 - (abs(self.x - x)) / 4000
            else:
                return -(0.2 - (abs(self.x - x)) / 4000)
        else:
            return 0

    def move_left(self):
        """
        Same thing as move right but checks that the spaceship does not go too far left outsdide
        :return: None
        """
        if self.x - self.SPACESHIP_VELOCITY > 0:
            self.x -= self.SPACESHIP_VELOCITY
            asteroid = self.available_asteroids[0]
            '''x = asteroid.x + math.tan(asteroid.angle) * (self.y - asteroid.y)
            if self.x - self.SPACESHIP_VELOCITY > x:
                return 0.1 - (abs(self.x - x)) / 4000
            else:
                return -(0.1 - (abs(self.x - x)) / 4000)'''
            x = asteroid.rect.center[0] + (
                    (self.y - asteroid.rect.center[1]) / (1 + math.cos(asteroid.angle))) * math.sin(asteroid.angle)
            # x = asteroid.rect.center[0]
            if self.x + self.SPACESHIP_VELOCITY >= x:
                return 0.1 - (abs(self.x - x)) / 4000
            else:
                return -(0.2 - (abs(self.x - x)) / 4000)
        else:
            return 0

    def shoot(self):
        """
        allows us to shoot a bullet only twice per second and a maximum number of bullets.
        bullet is just a rectangle with bullet dimensions and starting position in the middle of the spaceship
        :return: None
        """
        if self.tick >= 50:
            if len(self.bullets) <= self.MAX_BULLETS:
                bullet = pygame.Rect(self.x + self.width // 2, self.y - self.BULLET_HEIGHT, self.BULLET_WIDTH,
                                     self.BULLET_HEIGHT)
                self.bullets.append(bullet)
                self.tick = 0

    def draw(self):
        """
        makes a rectangle for the ship and blits it
        checks through the bullets if any have gone above the screen and adds them to remove and deletes them afterward
        otherwise it moves the bullet up and draws it
        :return: None
        """
        ship_rect = pygame.Rect(self.x, self.y, self.width, self.height)
        self.tick += 1

        for bullet in self.bullets:
            bullet.y -= self.BULLET_VELOCITY
            pygame.draw.rect(WIN, BULLET_COLOR, bullet)

        WIN.blit(self.IMG, ship_rect.topleft)

    def get_mask(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)

    def __repr__(self):
        return "Ship at " + str(self.x)


class Asteroid:
    VELOCITY = 5

    def __init__(self):
        """
        sets up the asteroid. We take it to be a square with a random length and random starting position. We displace
        it above by its length, so it starts from the top.
        """
        self.length = random.randrange(50, 100, 5)
        self.x = random.randint(SPACESHIP_WIDTH // 2, WIN_WIDTH - SPACESHIP_WIDTH // 2)
        self.y = -self.length
        self.IMG = pygame.transform.scale(ASTEROID_IMG, (self.length, self.length))
        self.target_x = random.randint(0, WIN_WIDTH)  # Random coordinate to go to
        self.angle = math.atan((self.target_x - self.x) / (WIN_HEIGHT + self.length))  # gets an angle to aim
        self.IMG = pygame.transform.rotate(self.IMG, self.angle)
        self.rect = pygame.Rect(self.x, self.y, self.length, self.length)

    def move(self):
        """
        Deletes the asteroid if it goes below the screen otherwise it moves the asteroid such that the angle is
        maintained :return: None
        """
        if self.y > 450 + self.length:
            pygame.event.post(pygame.event.Event(DEL_ASTEROID))
        else:
            self.x += self.VELOCITY * math.sin(self.angle)
            self.y += self.VELOCITY * math.cos(self.angle)
            self.rect = pygame.Rect(self.x, self.y, self.length, self.length)
            WIN.blit(self.IMG, self.rect.topleft)

    def get_mask(self):
        """
        :return: Rectangle of the asteroid to use for collisions
        """
        return pygame.Rect(self.x, self.y, self.length, self.length)

    def __repr__(self):
        return 'Asteroid ' + str(self.x)


def draw_window(ships, asteroids, ge, nets):
    """
    updates the window and checks for collisions between bullets and asteroids as well as asteroids and spaceship
    then it increases/decreases the fitness and removes the bullets and asteroids that have collided and also the
    spaceships and their neural networks also updates the score
    :param ships: list of spaceships
    :param asteroids: list of asteroids
    :param ge: list of genomes
    :param nets: list of neural networks
    :return: None
    """
    global numasteroids
    WIN.blit(BACKGROUND_IMG, (0, 0))
    score = SCORE_FONT.render('Score: ' + str(numasteroids), True, WHITE)
    numShips = SCORE_FONT.render('Ships: ' + str(len(ships)), True, WHITE)
    WIN.blit(score, (10, 10))
    WIN.blit(numShips, (10, 45))

    for asteroid in asteroids:
        asteroid.move()
    for ship in ships:  # moves each ship
        ship.draw()

    for asteroid in asteroids:
        rembullets = []
        remship = []
        # remasteroids = []
        for x, ship in enumerate(ships):
            rembullets.append([])
            for bullet in ship.bullets:
                if bullet.colliderect(asteroid.get_mask()) and asteroid in ship.available_asteroids:
                    ship.score += 1
                    ge[x].fitness += 5
                    ship.available_asteroids.remove(asteroid)
                    # remasteroids.append(asteroid)
                    rembullets[-1].append(bullet)

            if ship.get_mask().colliderect(asteroid.get_mask()) and asteroid in ship.available_asteroids:
                ship.score -= 5
                ge[x].fitness -= 4
                remship.append(x)

        # for asteroid in remasteroids:
        #    asteroids.remove(asteroid)
        for x in remship[::-1]:  # we remove in reverse so that the indexes don't change
            ge.pop(x)
            ships.pop(x)
            nets.pop(x)
            rembullets.pop(x)

        for index, group in enumerate(rembullets):  # Remove bullets for each spaceship
            if group:
                for bullet in group:
                    if bullet:
                        ships[index].bullets.remove(bullet)

        for x, ship in enumerate(ships):
            for bullet in ship.bullets:
                if bullet.y < -ship.BULLET_HEIGHT:
                    ship.bullets.remove(bullet)
                    ge[x].fitness -= 0.1

    pygame.display.update()


numasteroids = 0


def main(genomes, config):
    global numasteroids
    numasteroids = 0
    ships = []
    nets = []
    ge = []

    for _, g in genomes:
        net = neat.nn.FeedForwardNetwork.create(g, config)
        nets.append(net)
        ships.append(Spaceship(200, 450))
        g.fitness = 0
        ge.append(g)

    pygame.time.Clock()
    run = True
    asteroids = []
    count = 0
    while run:
        # clock.tick(FPS)
        count += 1

        for x, g in enumerate(ge):
            # g.fitness += 0.005
            if g.fitness <= -100:
                g.fitness -= 10
                ships.pop(x)
                nets.pop(x)
                ge.pop(x)
            else:
                if ships[x].available_asteroids:
                    asteroid = ships[x].available_asteroids[0]
                    output = nets[x].activate((asteroid.rect.center[0], asteroid.rect.center[1],
                                               asteroid.angle, ships[x].x, ships[x].y))

                    if output[0] > 0:
                        # g.fitness += ships[x].move_right()
                        ships[x].move_right()
                    elif output[0] < 0:
                        # g.fitness += ships[x].move_left()
                        ships[x].move_left()
                    if output[1] <= 0:
                        ships[x].shoot()

        for event in pygame.event.get():
            if event.type == DEL_ASTEROID:
                asteroid = asteroids.pop(0)
                for x, ship in enumerate(ships):
                    if asteroid in ship.available_asteroids:
                        ship.available_asteroids.remove(asteroid)
                        ge[x].fitness -= 2
                        ships.pop(x)
                        ge.pop(x)
                        nets.pop(x)

            if event.type == pygame.QUIT:
                g = []
                for gen in ge:
                    g.append(gen.fitness)

                dot = ge[g.index(max(g))]
                with open('neuralNetworkc', 'wb') as f:
                    pickle.dump(dot, f)
                quit()
                run = False

        if count >= 80:
            asteroid = Asteroid()
            asteroids.append(asteroid)
            numasteroids += 1
            for ship in ships:
                ship.available_asteroids.append(asteroid)
            count = 0
        draw_window(ships, asteroids, ge, nets)
        if len(ships) <= 0:
            run = False
            break
        if numasteroids > 1500:
            break


def run(config_path):
    """
    RUns neat and evolves the neural network as per the configurations
    finds the best nn and pickles it
    :param config_path: fiole path to configuration file
    :return: None
    """
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction,
                                neat.DefaultSpeciesSet, neat.DefaultStagnation,
                                config_path)
    p = neat.Population(config)
    p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)

    winner = p.run(main, 500)
    with open('neuralNetwork1', 'wb') as f:
        pickle.dump(winner, f)


if __name__ == '__main__':
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, 'config-feedforward.txt')
    run(config_path)

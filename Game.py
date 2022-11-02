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
SCORE_FONT = pygame.font.SysFont('comicsans', 30)
GAMEO_FONT = pygame.font.SysFont('comicsans', 40)
TEXT_FONT = pygame.font.SysFont('comicsans', 20)
DEL_ASTEROID = pygame.USEREVENT + 1

SPACESHIP_HEIGHT = 50
SPACESHIP_WIDTH = 69

SPACESHIP_IMG = pygame.image.load(os.path.join('Assets', 'spaceship.png'))
SPACESHIP_IMG = pygame.transform.scale(SPACESHIP_IMG, (SPACESHIP_WIDTH, SPACESHIP_HEIGHT))
SPACESHIP_IMG = pygame.transform.rotate(SPACESHIP_IMG, 180)

ASTEROID_IMG = pygame.image.load(os.path.join('Assets', 'asteroid.png'))
HEART_IMG = pygame.image.load(os.path.join('Assets', 'heart.png'))
HEART_IMG = pygame.transform.scale(HEART_IMG, (SPACESHIP_HEIGHT, SPACESHIP_HEIGHT))

BACKGROUND_IMG = pygame.image.load(os.path.join('Assets', 'space.png'))

GAMEOVER_BOX = pygame.image.load(os.path.join('Assets', 'border.png'))
GAMEOVER_BOX = pygame.transform.scale(GAMEOVER_BOX, (WIN_HEIGHT - 150, GAMEOVER_BOX.get_height()))
LEADERBOARD_BOX = pygame.image.load(os.path.join('Assets', 'border.png'))
LEADERBOARD_BOX = pygame.transform.rotate(LEADERBOARD_BOX, 90)
LEADERBOARD_BOX = pygame.transform.scale(LEADERBOARD_BOX, (WIN_WIDTH + 140, WIN_HEIGHT + 140))

with open('neuralNetwork', 'rb') as f:
    g = pickle.load(f)
local_dir = os.path.dirname(__file__)
config_path = os.path.join(local_dir, 'config-feedforward.txt')
config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction,
                            neat.DefaultSpeciesSet, neat.DefaultStagnation,
                            config_path)
net = neat.nn.FeedForwardNetwork.create(g, config)


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
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        self.bullets = []
        self.tick = 0
        self.score = 0
        self.available_asteroids = []
        self.aimBot = False

    def move_right(self):
        """
        moves the spaceship right as long as its right side does not go out of the screen
        :return: None
        """
        if self.x + self.SPACESHIP_VELOCITY + self.width < WIN_WIDTH:
            self.x += self.SPACESHIP_VELOCITY

    def move_left(self):
        """
        Same thing as move right but checks that the spaceship does not go too far left outsdide
        :return: None
        """
        if self.x - self.SPACESHIP_VELOCITY + 1 > 0:
            self.x -= self.SPACESHIP_VELOCITY

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
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        self.tick += 1

        remove = []
        for bullet in self.bullets:
            if bullet.y < -self.BULLET_HEIGHT:
                remove.append(bullet)
            else:
                bullet.y -= self.BULLET_VELOCITY
                pygame.draw.rect(WIN, BULLET_COLOR, bullet)
        for elem in remove:
            self.bullets.remove(elem)

        WIN.blit(self.IMG, self.rect.topleft)

    def get_mask(self):
        """
        :return: Rectangle of the spaceship to use for collisions
        """
        return pygame.Rect(self.x, self.y, self.width, self.height)

    def aim_bot(self):
        """
        Finds out the position of where the spaceship should be to hit it and moves there
        :return: None
        """
        if self.aimBot:
            if self.available_asteroids:
                asteroid = self.available_asteroids[0]
                output = net.activate(
                    (asteroid.rect.center[0], asteroid.rect.center[1], asteroid.angle, self.x, self.y))
                if output[0] > 0:
                    self.move_right()
                elif output[0] < 0:
                    self.move_left()
                if output[1] <= 0:
                    self.shoot()


class Asteroid:
    VELOCITY = 5

    def __init__(self):
        """
        sets up the asteroid. We take it to be a square with a random length and random starting position. We displace
        it above by its length, so it starts from the top.
        """
        self.length = random.randrange(50, 100, 5)
        self.x = random.randint(0, WIN_WIDTH - self.length)
        self.y = -self.length
        self.IMG = pygame.transform.scale(ASTEROID_IMG, (self.length, self.length))
        self.target_x = random.randint(SPACESHIP_WIDTH // 2,
                                       WIN_WIDTH - SPACESHIP_WIDTH // 2)  # Random coordinate to go to
        self.angle = math.atan((self.target_x - self.x) / (450 + self.length))  # gets an angle to aim
        self.IMG = pygame.transform.rotate(self.IMG, self.angle)  # Random rotation
        self.rect = pygame.Rect(self.x, self.y, self.length, self.length)

    def move(self):
        """
        Deletes the asteroid if it goes below the screen otherwise it moves the asteroid such that the angle is
        maintained
        :return: None
        """
        if self.y > WIN_HEIGHT:
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


def leader_board(ship):
    """
    displays the leader board First opens the file with the scores and gets them into a list form of integers. Then
    displays them along with instructions
    :param ship: spaceship
    :return: 1 if user wants to restart else none
    """
    run = True
    FPS = 60
    clock = pygame.time.Clock()

    # reads the scores then splits them into individual scores and converts to int
    f = open('leaderBoard.txt', 'r')
    scores = f.read().split()
    curScore = ship.score
    scores = list(map(lambda x: int(x), scores))
    f.close()

    while run:
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False

        keys = pygame.key.get_pressed()

        # Exits if enter is press and restarts when R is pressed
        if keys[pygame.K_RETURN]:
            run = False
        elif keys[pygame.K_r]:
            return 1

        # Positions the leaderboard box in the middle of the screen
        box_x, box_y = (WIN_WIDTH - LEADERBOARD_BOX.get_width()) // 2, (WIN_HEIGHT - LEADERBOARD_BOX.get_height()) // 2
        WIN.blit(LEADERBOARD_BOX, (box_x, box_y))

        title = GAMEO_FONT.render('LEADERBOARD', True, WHITE)
        instruction = TEXT_FONT.render('Press Enter to Exit or R to restart', True, WHITE)

        # Loads the scores with positions and also shows your scores
        s1 = SCORE_FONT.render('1.  ' + str(scores[0]), True, WHITE)
        s2 = SCORE_FONT.render('2.  ' + str(scores[1]), True, WHITE)
        s3 = SCORE_FONT.render('3.  ' + str(scores[2]), True, WHITE)
        s4 = SCORE_FONT.render('4.  ' + str(scores[3]), True, WHITE)
        s5 = SCORE_FONT.render('5.  ' + str(scores[4]), True, WHITE)
        s6 = SCORE_FONT.render('6.  ' + str(scores[5]), True, WHITE)
        s7 = SCORE_FONT.render('7.  ' + str(scores[6]), True, WHITE)
        s8 = SCORE_FONT.render('8.  ' + str(scores[7]), True, WHITE)
        s9 = SCORE_FONT.render('9.  ' + str(scores[8]), True, WHITE)
        s10 = SCORE_FONT.render('Your Score: ' + str(curScore), True, WHITE)

        # Blits all the elements with 40 spaces between each
        WIN.blit(title, (box_x + (LEADERBOARD_BOX.get_width() - title.get_width()) // 2, box_y + 110))
        WIN.blit(s1, (box_x + (LEADERBOARD_BOX.get_width() - s1.get_width()) // 2, box_y + 170))
        WIN.blit(s2, (box_x + (LEADERBOARD_BOX.get_width() - s2.get_width()) // 2, box_y + 210))
        WIN.blit(s3, (box_x + (LEADERBOARD_BOX.get_width() - s3.get_width()) // 2, box_y + 250))
        WIN.blit(s4, (box_x + (LEADERBOARD_BOX.get_width() - s4.get_width()) // 2, box_y + 290))
        WIN.blit(s5, (box_x + (LEADERBOARD_BOX.get_width() - s5.get_width()) // 2, box_y + 330))
        WIN.blit(s6, (box_x + (LEADERBOARD_BOX.get_width() - s6.get_width()) // 2, box_y + 370))
        WIN.blit(s7, (box_x + (LEADERBOARD_BOX.get_width() - s7.get_width()) // 2, box_y + 410))
        WIN.blit(s8, (box_x + (LEADERBOARD_BOX.get_width() - s8.get_width()) // 2, box_y + 450))
        WIN.blit(s9, (box_x + (LEADERBOARD_BOX.get_width() - s9.get_width()) // 2, box_y + 490))
        WIN.blit(s10, (box_x + (LEADERBOARD_BOX.get_width() - s10.get_width()) // 2, box_y + 530))

        WIN.blit(instruction, (box_x + (LEADERBOARD_BOX.get_width() - instruction.get_width()) // 2, box_y + 590))
        pygame.display.update()


def game_over(ship):
    """
    Shows the game over display and stops the game from running fursther till something is done
    :param ship: spaceship
    :return: 1 to restart the game else none
    """
    run = True
    FPS = 60
    clock = pygame.time.Clock()

    # Opens the file and gets a list of all the leaderboard scores
    f = open('leaderBoard.txt', 'r+')
    scores = f.read().split()
    curScore = ship.score
    scores = list(map(lambda x: int(x), scores))

    # Compares if the current score will be in the leaderboard and adds it in its position
    if curScore >= min(scores):
        for s in scores:
            if curScore > s:
                scores.pop()
                scores.insert(1, curScore)
                scores.sort(reverse=True)
                break

    # Empties the file contents and adds the updated leaderboard in formatted form
    f.truncate(0)
    f.seek(0)
    for i in scores:
        f.write(str(i) + ' ')
    f.close()

    while run:
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False

        keys = pygame.key.get_pressed()

        # Calls the leaderboard function if l is pressed, exits if enter is pressed and returns 1 to restart if r is
        # pressed
        if keys[pygame.K_l]:
            return leader_board(ship)
        elif keys[pygame.K_RETURN]:
            run = False
        elif keys[pygame.K_r]:
            return 1

        box_x, box_y = (WIN_WIDTH - GAMEOVER_BOX.get_width()) / 2, (WIN_HEIGHT - GAMEOVER_BOX.get_height()) / 2
        WIN.blit(GAMEOVER_BOX, (box_x, box_y))

        gameover = GAMEO_FONT.render('GAME OVER', True, WHITE)
        instructions1 = TEXT_FONT.render('Press L for leaderboard', True, WHITE)
        instructions2 = TEXT_FONT.render('or Enter to exit or R to restart', True, WHITE)

        WIN.blit(gameover, (box_x + (GAMEOVER_BOX.get_width() - gameover.get_width()) / 2, box_y + 110))
        WIN.blit(instructions1, (
            box_x + (GAMEOVER_BOX.get_width() - instructions1.get_width()) / 2, box_y + gameover.get_height() + 130))
        WIN.blit(instructions2, (
            box_x + (GAMEOVER_BOX.get_width() - instructions2.get_width()) / 2, box_y + gameover.get_height() + 155))
        pygame.display.update()


def draw_window(ship, asteroids):
    """
    updates the window and checks for collisions between bullets and asteroids as well as asteroids and spaceship
    then it increases/decreases the score and removes the bullets and asteroids that have collided
    also updates the score
    :param ship: spaceship
    :param asteroids: list of asteroids
    :return: None
    """
    global lives

    WIN.blit(BACKGROUND_IMG, (0, 0))
    score = SCORE_FONT.render('Score: ' + str(ship.score), True, WHITE)
    WIN.blit(score, (15, 15))

    # moves all the asteroids
    for asteroid in asteroids:
        asteroid.move()
    ship.aim_bot()
    ship.draw()

    # We delete the bullets and asteroids at the end so that problems don't arise due to them being deleted while
    # looping through a list
    rembullets = []
    remasteroids = []

    # Checks for bullets that have hit an asteroid and deletes them and increments the score
    for asteroid in asteroids:
        for bullet in ship.bullets:
            if bullet.colliderect(asteroid.get_mask()):
                ship.score += 1
                remasteroids.append(asteroid)
                rembullets.append(bullet)

        # If an asteroid hits a ship one life is removed
        if ship.get_mask().colliderect(asteroid.get_mask()):
            lives.pop()
            if asteroid not in remasteroids:
                remasteroids.append(asteroid)

    for heart in lives:
        WIN.blit(HEART_IMG, heart)

    # removes the collided bullets and asteroids
    for asteroid in remasteroids:
        asteroids.remove(asteroid)
        ship.available_asteroids.remove(asteroid)
    for bullet in rembullets:
        ship.bullets.remove(bullet)

    pygame.display.update()


def key_update(keys, ship):
    """
    Checks for the key inputs and moves the spaceship accordingly
    :param keys: dictionary of keys pressed
    :param ship: spaceship
    :return: None
    """
    if keys[pygame.K_SPACE]:
        ship.shoot()
    if not ship.aimBot:
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            ship.move_left()
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            ship.move_right()


def main():
    """
    Main loop that runs the game and checks for key updates, gameover, etc.
    :return: 1 to restart else none
    """
    fps = 60
    clock = pygame.time.Clock()
    run = True
    ship = Spaceship(100, 450)
    count = 0
    global asteroids

    while run:
        clock.tick(fps)
        count += 1
        fps += 0.01  # We increment the fps so that the speed increases over time

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False

            # If an asteroid goes out of the screen we pop the first asteroid in the list since it spawned first
            if event.type == DEL_ASTEROID:
                asteroid = asteroids.pop(0)
                ship.available_asteroids.remove(asteroid)

        keys = pygame.key.get_pressed()
        key_update(keys, ship)

        # Turns the aimbot on or off
        if keys[pygame.K_n]:
            if ship.aimBot:
                ship.aimBot = False
            else:
                ship.aimBot = True

        # Spawns a new asteroid every 80 frames and adds a life for every 100 points
        if count == 80:
            asteroids.append(Asteroid())
            ship.available_asteroids.append(asteroids[-1])
            count = 0
            if ship.score % 100 == 0 and ship.score != 0 and len(lives) < 3:
                x, y = lives[-1]
                lives.append((x + 50, y))
                count = 20
        draw_window(ship, asteroids)

        # When lives run out we go to game over and the function ends
        if len(lives) == 0:
            return game_over(ship)

    pygame.quit()
    quit()


if __name__ == '__main__':
    run = True

    while run:
        asteroids = []
        lives = [(10, 60), (60, 60), (110, 60)]
        # lives = [(0,0)]
        run = main()

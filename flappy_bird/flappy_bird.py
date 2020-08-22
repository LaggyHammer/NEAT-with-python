import pygame
import neat
import os
import random
import pickle

pygame.font.init()

WIN_WIDTH = 600
WIN_HEIGHT = 800
FLOOR = 730
STAT_FONT = pygame.font.SysFont("comicsans", 50)
DRAW_LINES = False

WIN = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
pygame.display.set_caption("NEAT - Flappy Bird")

BIRD_IMAGES = [pygame.transform.scale2x(pygame.image.load(os.path.join("assets", "bird" + str(x) + ".png"))) for x in
               range(1, 4)]
PIPE_IMAGE = pygame.transform.scale2x(pygame.image.load(os.path.join("assets", "pipe.png")).convert_alpha())
BASE_IMAGE = pygame.transform.scale2x(pygame.image.load(os.path.join("assets", "base.png")).convert_alpha())
BKG_IMAGE = pygame.transform.scale(pygame.image.load(os.path.join("assets", "bg.png")).convert_alpha(), (600, 900))

generation = 0


class Bird:
    IMAGES = BIRD_IMAGES
    MAX_ROTATION = 25
    ROT_VEL = 20
    ANIMATION_TIME = 5

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.tilt = 0
        self.tick_count = 0
        self.vel = 0
        self.height = self.y
        self.img_count = 0
        self.img = self.IMAGES[0]

    def jump(self):
        self.vel = -10.5
        self.tick_count = 0
        self.height = self.y

    def move(self):
        self.tick_count += 1

        d = self.vel * self.tick_count + 1.5 * self.tick_count ** 2

        if d >= 16:
            d = 16
        if d < 0:
            d -= 2

        self.y += d

        if d < 0 or self.y < self.height + 50:
            if self.tilt < self.MAX_ROTATION:
                self.tilt = self.MAX_ROTATION

        else:
            if self.tilt > -90:
                self.tilt -= self.ROT_VEL

    def draw(self, win):
        self.img_count += 1

        if self.img_count < self.ANIMATION_TIME:
            self.img = self.IMAGES[0]
        elif self.img_count < self.ANIMATION_TIME * 2:
            self.img = self.IMAGES[1]
        elif self.img_count < self.ANIMATION_TIME * 3:
            self.img = self.IMAGES[2]
        elif self.img_count < self.ANIMATION_TIME * 4:
            self.img = self.IMAGES[1]
        elif self.img_count < self.ANIMATION_TIME * 4 + 1:
            self.img = self.IMAGES[0]
            self.img_count = 0

        if self.tilt <= -80:
            self.img = self.IMAGES[1]
            self.img_count = self.ANIMATION_TIME * 2

        rotated_image = pygame.transform.rotate(self.img, self.tilt)
        new_rectangle = rotated_image.get_rect(center=self.img.get_rect(topleft=(int(self.x), int(self.y))).center)
        win.blit(rotated_image, new_rectangle.topleft)

    def get_mask(self):
        return pygame.mask.from_surface(self.img)


class Pipe:
    GAP = 250
    VEL = 5

    def __init__(self, x):
        self.x = x
        self.height = 0

        self.top = 0
        self.bottom = 0
        self.PIPE_TOP = pygame.transform.flip(PIPE_IMAGE, False, True)
        self.PIPE_BOTTOM = PIPE_IMAGE

        self.passed = False
        self.set_height()

    def set_height(self):
        self.height = random.randrange(50, 450)
        self.top = self.height - self.PIPE_TOP.get_height()
        self.bottom = self.height + self.GAP

    def move(self):
        self.x -= self.VEL

    def draw(self, win):
        win.blit(self.PIPE_TOP, (self.x, self.top))
        win.blit(self.PIPE_BOTTOM, (self.x, self.bottom))

    def collide(self, bird):
        bird_mask = bird.get_mask()
        top_mask = pygame.mask.from_surface(self.PIPE_TOP)
        bottom_mask = pygame.mask.from_surface(self.PIPE_BOTTOM)

        top_offset = (self.x - bird.x, self.top - round(bird.y))
        bottom_offset = (self.x - bird.x, self.bottom - round(bird.y))

        b_point = bird_mask.overlap(bottom_mask, bottom_offset)
        t_point = bird_mask.overlap(top_mask, top_offset)

        if t_point or b_point:
            return True

        return False


class Base:
    VEL = 5
    WIDTH = BASE_IMAGE.get_width()
    IMG = BASE_IMAGE

    def __init__(self, y):
        self.y = y
        self.x1 = 0
        self.x2 = self.WIDTH

    def move(self):
        self.x1 -= self.VEL
        self.x2 -= self.VEL

        if self.x1 + self.WIDTH < 0:
            self.x1 = self.x2 + self.WIDTH
        if self.x2 + self.WIDTH < 0:
            self.x2 = self.x1 + self.WIDTH

    def draw(self, win):
        win.blit(self.IMG, (self.x1, self.y))
        win.blit(self.IMG, (self.x2, self.y))


def draw_window(win, birds, pipes, base, score, gen, pipe_ind):
    if gen == 0:
        gen = 1

    win.blit(BKG_IMAGE, (0, 0))

    for pipe in pipes:
        pipe.draw(win)

    base.draw(win)

    for bird in birds:
        if DRAW_LINES:
            try:
                pygame.draw.line(win, (255, 0, 0),
                                 (bird.x + bird.img.get_width() / 2, bird.y + bird.img.get_height() / 2),
                                 (pipes[pipe_ind].x + pipes[pipe_ind].PIPE_TOP.get_width() / 2, pipes[pipe_ind].height),
                                 5)
                pygame.draw.line(win, (255, 0, 0),
                                 (bird.x + bird.img.get_width() / 2, bird.y + bird.img.get_height() / 2), (
                                     pipes[pipe_ind].x + pipes[pipe_ind].PIPE_BOTTOM.get_width() / 2,
                                     pipes[pipe_ind].bottom), 5)
            except Exception:
                pass
        bird.draw(win)

    text = STAT_FONT.render(f'Score: {str(score)}', 1, (255, 255, 255))
    win.blit(text, (WIN_WIDTH - 10 - text.get_width(), 10))

    text = STAT_FONT.render(f'Gen: {str(gen - 1)}', 1, (255, 255, 255))
    win.blit(text, (10, 10))

    text = STAT_FONT.render(f'Alive: {str(len(birds))}', 1, (255, 255, 255))
    win.blit(text, (10, 50))

    pygame.display.update()


def main(genomes, config):
    global WIN, generation
    win = WIN
    generation += 1

    nets = []
    ge = []
    birds = []

    for _, genome in genomes:
        genome.fitness = 0
        net = neat.nn.FeedForwardNetwork.create(genome, config)
        nets.append(net)
        birds.append(Bird(230, 350))
        ge.append(genome)

    base = Base(FLOOR)
    pipes = [Pipe(700)]
    score = 0

    clock = pygame.time.Clock()

    run = True
    while run and len(birds) > 0:
        clock.tick(30)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                pygame.quit()
                quit()
                break

        pipe_ind = 0
        if len(birds) > 0:
            if len(pipes) > 1 and birds[0].x > pipes[0].x + pipes[0].PIPE_TOP.get_width():
                pipe_ind = 1

        for x, bird in enumerate(birds):
            ge[x].fitness += 0.1
            bird.move()

            output = nets[birds.index(bird)].activate((bird.y,
                                                       abs(bird.y - pipes[pipe_ind].height),
                                                       abs(bird.y - pipes[pipe_ind].bottom)
                                                       ))
            if output[0] > 0.5:
                bird.jump()

        base.move()

        add_pipe = False
        rem_pipe = []
        for pipe in pipes:
            pipe.move()

            for bird in birds:
                if pipe.collide(bird):
                    ge[birds.index(bird)].fitness -= 1
                    nets.pop(birds.index(bird))
                    ge.pop(birds.index(bird))
                    birds.pop(birds.index(bird))

                if not pipe.passed and pipe.x < bird.x:
                    pipe.passed = True
                    add_pipe = True

            if pipe.x + pipe.PIPE_TOP.get_width() < 0:
                rem_pipe.append(pipe)

        if add_pipe:
            score += 1
            for genome in ge:
                genome.fitness += 5
            pipes.append(Pipe(WIN_WIDTH))

        for pipe in rem_pipe:
            pipes.remove(pipe)

        for bird in birds:
            if bird.y + bird.img.get_height() - 10 >= FLOOR or bird.y < 0:
                nets.pop(birds.index(bird))
                ge.pop(birds.index(bird))
                birds.pop(birds.index(bird))

        draw_window(win, birds, pipes, base, score, generation, pipe_ind)

        if score > 30:
            pickle.dump(nets[0], open("best_bird.pickle", "wb"))
            return nets[0]


def run_neat(path):
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction,
                                neat.DefaultSpeciesSet, neat.DefaultStagnation,
                                path)

    pop = neat.Population(config)

    pop.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    pop.add_reporter(stats)

    winner = pop.run(main, 50)

    print(f'Best Genome : {winner}')


if __name__ == '__main__':
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, "neat_config.txt")
    run_neat(config_path)

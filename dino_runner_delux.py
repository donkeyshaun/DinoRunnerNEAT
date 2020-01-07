import pygame as pg
import random
import os
import math
import neat
vec = pg.math.Vector2


win_x = 1000
win_y = 500
pg.init()
pg.display.set_caption("Dino Runner")
WIN = pg.display.set_mode((win_x, win_y))

DRAW_LINES = False #True - draws line to cactus
quit_game = False
spawn_flying = 10
vel = 10
gen = 0
dino_art = [pg.image.load("sprites/running_1.png").convert_alpha(), pg.image.load("sprites/standing.png").convert_alpha(),
            pg.image.load("sprites/running_2.png").convert_alpha(), pg.image.load("sprites/jump.png").convert_alpha(), 
            pg.image.load("sprites/duck.png").convert_alpha(), pg.image.load("sprites/duck_run_1.png").convert_alpha(), 
            pg.image.load("sprites/duck_run_2.png").convert_alpha()]
bg_art = pg.image.load("sprites/bg.png").convert()
ground_art = pg.image.load("sprites/ground.png").convert_alpha()
cacti_art = [pg.image.load("sprites/cacti_1.png").convert_alpha(), pg.image.load("sprites/cacti_2.png").convert_alpha(), pg.image.load(
    "sprites/cacti_3.png").convert_alpha(), pg.image.load("sprites/cacti_4.png").convert_alpha(), pg.image.load("sprites/cacti_5.png").convert_alpha()]
flying_dino = [pg.image.load("sprites/fly_up.png").convert_alpha(), pg.image.load("sprites/fly_down.png").convert_alpha()]
death_sound = pg.mixer.Sound("audio/death.wav")
STAT_FONT = pg.font.SysFont("comicsans", 50)

#PRINT NETWORK 
best_genome = 0


class Dino:
    ANIMATION_TIME = 1
    dino_art = dino_art
    MAX_HANGTIME = 5
    JUMP_TIMER = 10
    MAX_VEL = 50
    INIT_GRAVITY = 0
    MAX_COUTING_VEL = 2

    def __init__(self, x, y):
        self.y_zero = y
        self.x = x
        self.y = y
        self.img = self.dino_art[0]
        self.img_count = 0
        self.jump = False
        self.jump_hold = False
        self.vel = vec(0, 0)
        self.gravity = 15
        self.counting_vel = 0
        self.duck = False
        self.move_vel = 5

    def dino_jump(self):
        if self.vel.y < 0:
            self.vel.y = self.MAX_VEL

    def draw(self, win):

        if not self.jump:
            if self.duck:
                if self.img_count <= self.ANIMATION_TIME:
                    self.img = dino_art[4]
                elif self.img_count <= self.ANIMATION_TIME+1:
                    self.img = dino_art[5]
                elif self.img_count <= self.ANIMATION_TIME+2:
                    self.img = dino_art[6]
                elif self.img_count > self.ANIMATION_TIME+2:
                    self.img_count = 0
                self.y = self.y_zero+30
            else:
                self.y = self.y_zero
                if self.img_count <= self.ANIMATION_TIME:
                    self.img = dino_art[0]
                elif self.img_count <= self.ANIMATION_TIME+1:
                    self.img = dino_art[1]
                elif self.img_count <= self.ANIMATION_TIME+2:
                    self.img = dino_art[2]
                elif self.img_count > self.ANIMATION_TIME+2:
                    self.img_count = 0
            self.img_count += 1

        else:
            if self.img_count <= self.ANIMATION_TIME or self.img_count > 5:
                self.img = pg.transform.flip(dino_art[3], True, False)
            else:
                self.img = dino_art[3]
            self.img_count += 1

            if self.vel.y >= 0:
                self.y -= self.vel.y
                if self.jump_hold and -self.counting_vel < self.MAX_COUTING_VEL:
                    self.vel.y -= self.counting_vel + self.MAX_COUTING_VEL
                    self.counting_vel -= 2
                else:
                    self.vel.y -= self.counting_vel + 15
                    self.counting_vel += 1

            else:
                self.y += self.gravity
                self.gravity += 30
                if(self.y >= self.y_zero):
                    self.gravity = self.INIT_GRAVITY
                    self.y = self.y_zero
                    self.counting_vel = 0
                    self.jump = False
        win.blit(self.img, (self.x, self.y))

    def get_mask(self):
        return pg.mask.from_surface(self.img)


class Cactus:
    cacti_art = cacti_art
    flying_dino = flying_dino
    ANIMATION_TIME = 1

    def __init__(self):
        self.newObs = False
        self.x = win_x
        self.y = 330
        self.img = self.cacti_art[0]
        self.spawnTime = 10
        self.vel = 0
        self.spawn = 1
        self.img_count = 0
        self.flying_dino = False

    def set_vel(self, vel):
        self.vel = vel

    def moveLeft(self):
        if self.x >= -10-self.vel:
            self.x -= self.vel
        elif not self.flying_dino:
            self.x = random.randrange(win_x, win_x+self.vel)
            self.newObs = True

    def draw(self, win):

        if self.newObs:
            self.img = cacti_art[random.randrange(0, len(cacti_art))]
            if cacti_art.index(self.img) > 2:
                self.y = 350
            else:
                self.y = 330
            self.spawn += 1

            self.newObs = False
        
        if self.flying_dino:
            if self.img_count <= self.ANIMATION_TIME:
                self.img = flying_dino[0]
            elif self.img_count <= self.ANIMATION_TIME+1:
                self.img = flying_dino[1]
                self.newObs = False
                self.img_count = 0
        
            self.img_count += 1

        win.blit(self.img, (self.x, self.y))

    def collide(self, dino, win):

        dino_mask = dino.get_mask()
        cactus_mask = pg.mask.from_surface(self.img)

        offset = (round(self.x - dino.x), self.y - round(dino.y))
        b_point = dino_mask.overlap(cactus_mask, offset)

        if b_point:
            return True

        return False

class Ground:
    ground_art = ground_art

    def __init__(self, x):
        self.newObs = False
        self.x = x
        self.y = 0
        self.img = self.ground_art
        self.vel = 0

    def set_vel(self, vel):
        self.vel = vel

    def moveLeft(self):
        if self.x >= -win_x-self.vel:
            self.x -= self.vel
        else:
            self.x = win_x
            self.newObs = True

    def draw(self, win):

        win.blit(self.img, (self.x, self.y))

def drawNet(win, genome):
    y_graph = 0
    x_graph = 700
    input_nodes = 3
    output_nodes = 3
    circle_radius = 10
    y_offset = (circle_radius*2+circle_radius)
    x_offset = y_offset*2
    max_offset = y_offset*max([input_nodes,output_nodes])
    offset_pos = 0

    if genome != 0:
        #Draw circles
        node_layers = []
        layer = []
        for node in range(input_nodes):
            layer.append(-node-1)
        node_layers.append(layer)
        layer = []
        for node in genome.nodes:
            if node not in range(output_nodes):
                if len(layer) >= 4:
                    node_layers.append(layer)
                    layer = []
                layer.append(node)
        if len(layer) > 0:
            node_layers.append(layer)
        layer = []
        for node in range(output_nodes):
            layer.append(node)
        node_layers.append(layer)

        if len(node_layers) > 2:
            x_graph -= (len(node_layers)-2)*x_offset


        for layer_id in range(len(node_layers)):
            for node_id in range(len(node_layers[layer_id])):
                if node_id % 2 > 0:
                    offset_pos += 1
                pg.draw.circle(win,(255,0,0),(round(x_graph+x_offset*layer_id),round(y_graph+max_offset/2 + y_offset*offset_pos)),circle_radius)
                offset_pos = -offset_pos
            offset_pos = 0


        #Draw Connections
        for con in genome.connections:
            node_one_y = 0
            node_one_x = 0
            node_two_y = 0
            node_two_x = 0
            for layer_id in range(len(node_layers)):
                for node_id in range(len(node_layers[layer_id])):
                    temp = node_layers[layer_id]
                    if node_id % 2 > 0:
                        offset_pos += 1
                    if con[0] == temp[node_id]:
                        node_one_y = offset_pos
                        node_one_x = layer_id
                    if con[1] == temp[node_id]:
                        node_two_y = offset_pos
                        node_two_x = layer_id
                    offset_pos = -offset_pos
                offset_pos = 0
            pg.draw.line(win,(0,0,0), (round(x_graph+x_offset*node_one_x),round(y_graph+max_offset/2 + y_offset*node_one_y)),(round(x_graph+x_offset*node_two_x),round(y_graph+max_offset/2 + y_offset*node_two_y)), 2)


def draw_game(win, dinos, cacti, grounds, vel, score, gen, best_genome):
    win.blit(bg_art, (0, 0))
    global spawn_flying
    for ground in grounds:
        ground.draw(win)
        ground.set_vel(vel)
        ground.moveLeft()
    for cactus in cacti:
        if cactus.flying_dino and cactus.x < -20:
            cacti.remove(cactus)
        cactus.draw(win)
        cactus.set_vel(vel)
        cactus.moveLeft()
    if cacti[0].spawn % 10 == 0 and len(cacti) == 1:
        flying_dino = Cactus()
        flying_dino.x = cacti[0].x + win_x/2
        flying_dino.y = random.randrange(290,300)
        flying_dino.flying_dino = True
        cacti.append(flying_dino)

    for dino in dinos:
        dino.draw(win)
        if DRAW_LINES:
            try:
                pg.draw.line(win, (255, 0, 0), (dino.x+100, dino.y),
                             (cacti[0].x+30, cacti[0].y), 5)
            except:
                pass

    drawNet(win, best_genome)

    # score
    score_label = STAT_FONT.render("Score: " + str(score), 1, (255, 0, 0))
    win.blit(score_label, (10, 10))

    # generations
    score_label = STAT_FONT.render("Gene: " + str(gen-1), 1, (255, 0, 0))
    win.blit(score_label, (10, 50))

    # alive
    score_label = STAT_FONT.render("Alive: " + str(len(dinos)), 1, (255, 0, 0))
    win.blit(score_label, (10, 90))

    pg.display.update()


def eval_genomes(genomes, config):
    global gen, WIN, quit_game, best_genome
    win = WIN
    gen += 1
    score = 0
    speed = 20
    timer = 0
    clock = pg.time.Clock()
    ge = []
    nets = []
    dinos = []
    for genome_id, genome in genomes:
        genome.fitness = 0  # start with fitness level of 0
        net = neat.nn.FeedForwardNetwork.create(genome, config)
        nets.append(net)
        dinos.append(Dino(50, 330))
        ge.append(genome)
    cacti = [Cactus()]
    grounds = [Ground(0), Ground(1000)]
    while dinos != [] and not quit_game:
        clock.tick(30)

        draw_game(win, dinos, cacti, grounds, speed, score, gen, best_genome)

        if timer/50 == 1:
            speed += 2
            timer = 0
        timer += 1
        score += 1

        # give each dino a fitness of 1 for each frame it stays alive
        for x, dino in enumerate(dinos):
            ge[dinos.index(dino)].fitness += 1
            #distance = math.sqrt((dino.x+50 - cacti[0].x+30)**2 + (dino.y+100 - cacti[0].y)**2)
            distance_cactus = abs(dino.x+50 - cacti[0].x+30)
            distance_flying_dino = 0

            if(dino.x+50 > cacti[0].x+30):
                distance_cactus = -distance_cactus
            
            if len(cacti) > 1:
                distance_flying_dino = math.sqrt((dino.x+50 - cacti[1].x+30)**2 + (dino.y+100 - cacti[1].y)**2)

                

            # print(distance)
            output = nets[dinos.index(dino)].activate([distance_cactus, distance_flying_dino, speed])
            if output[0] > 0.5:
                dino.jump_hold = True
                if dino.jump == False:
                    dino.dino_jump()
                    dino.jump = True
                    dino.jump_hold = True
            elif output[0] > 0:
                if dino.jump == False:
                    dino.dino_jump()
                    dino.jump = True
                    dino.jump_hold = False
                    ge[dinos.index(dino)].fitness -= 5
                pass
            else:
                dino.jump_hold = False
            if output[1] > 0.5:
                dino.duck = True
                ge[dinos.index(dino)].fitness -= 1
            else:
                dino.duck = False
            if output[2] > 0.5:
                if dino.x - dino.move_vel < win_x:
                    dino.x +=  dino.move_vel
            
            if output[2] < -0.5:
                if dino.x - dino.move_vel > 0:
                    dino.x -= dino.move_vel 

        # COLLISION
        for cactus in cacti:
            deaths = len(dinos)
            for dino in dinos:
                if cactus.collide(dino, win):
                    ge[dinos.index(dino)].fitness -= 10
                    nets.pop(dinos.index(dino))
                    ge.pop(dinos.index(dino))
                    dinos.pop(dinos.index(dino))
            if len(dinos) < deaths:
                death_sound.play()

        for event in pg.event.get():
            if event.type == pg.QUIT:
                quit_game = True
                pg.quit()
    best_fitness = 0 
    for genome_id, genome in genomes:
        if genome.fitness > best_fitness:
            best_fitness = genome.fitness
            best_genome = genome


def run(config_file):
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction,
                                neat.DefaultSpeciesSet, neat.DefaultStagnation,
                                config_file)

    # Create the population, which is the top-level object for a NEAT run.
    p = neat.Population(config)

    # Add a stdout reporter to show progress in the terminal.
    p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)
    # p.add_reporter(neat.Checkpointer(5))

    # Run for up to x generations.
    winner = p.run(eval_genomes, 100)

    # show final stats
    print('\nBest genome:\n{!s}'.format(winner))


if __name__ == '__main__':
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, 'config-feedforward.txt')
    run(config_path)

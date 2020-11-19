import pygame
import time
import os
import random
import csv
import numpy as np
import matplotlib.pyplot as plt
from bird import Bird
from pipe import Pipe
from base import Base
from controller import Controller
import cvxpy as cp

pygame.font.init() # initialize fonts

WIN_WIDTH = 500
WIN_HEIGHT = 800

BG_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs","bg.png")))
STAT_FONT = pygame.font.SysFont('Comic Sans MS', 35)
STAT_FONT.set_bold(True)

def pipe_in_front(bird, pipes):

    # determine which pipe is in the fron of the bird
    if bird.x < pipes[0].x + pipes[0].PIPE_TOP.get_width():
        pipe = pipes[0]
    else:
        pipe = pipes[-1]
        
    return pipe

def draw_diagnostics(surface, bird, pipes):

    pipe = pipe_in_front(bird, pipes)

    # extract bird and pipe positions
    bird_position = bird.physical_position()
    _, pipe_end_position = pipe.physical_position()
    pipe_end_top, pipe_end_bottom = pipe_end_position

    # draw constrained region between the pipes
    pygame.draw.line(surface, (255,100,0), (bird_position[0] - 40, pipe_end_top[1]), pipe_end_top, 4)
    pygame.draw.line(surface, (255,100,0), (bird_position[0] - 40, pipe_end_bottom[1]), pipe_end_bottom ,4)

def draw_window(win, bird, pipes, base, score, diagnostics=False):
    win.blit(BG_IMG, (0,0))

    for pipe in pipes:
        pipe.draw(win)

    text = STAT_FONT.render('Score: ' + str(score), 1, (50,50,50))
    win.blit(text, (10, 10))

    base.draw(win)
    bird.draw(win)

    if diagnostics:
        # draw lines from the bird to the pipes
        surface = pygame.display.get_surface()
        draw_diagnostics(surface, bird, pipes)

    pygame.display.update()

def main():

        bird = Bird(230,350)
        base = Base(730)
        pipes = [Pipe(600)]
        controller = Controller(15,3)
        win = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
        clock = pygame.time.Clock()

        score = 0
        alive = True
        diagnostics = True

        while(alive):
            clock.tick(30) # perform iterations every 30ms

            # check whether user requested the game to end
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    quit()

            bird_position = bird.physical_position() # get bird state
            # get pipe position
            pipe = pipe_in_front(bird, pipes)
            pipe_start_position, _ = pipe.physical_position()
            pipe_start_top, pipe_start_bottom = pipe_start_position

            x0 = np.array([bird_position[0], bird_position[1], bird_position[2]])
            limits = np.array([pipe_start_bottom[1], pipe_start_top[1]])

            jump = controller.solve(x0, limits)

            # save current input data
            if jump:
                bird.jump()

            bird.move() # move the bird
            add_pipe = False
            rem = []
            for pipe in pipes:

                # if bird collided, kill the bird
                if pipe.collide(bird):
                    alive = False
                    break

                # if you are inside a pipe, consider it passed (unless you hit it, but it is handled as a collide event)
                if not pipe.passed and pipe.x < bird.x:
                    pipe.passed = True
                    add_pipe = True

                # append pipe to the remove list once it is fully passed
                if pipe.x + pipe.PIPE_TOP.get_width() < 0:
                    rem.append(pipe)

                pipe.move()

            if add_pipe:
                score += 1
                pipes.append(Pipe(600))

            for r in rem:
                pipes.remove(r)

            # if bird hit the bottom or the top of the screen, kill the bird
            if bird.y + bird.img.get_height() > 730 or bird.y < 0 or not alive:
                break

            base.move() # move the base
            draw_window(win, bird, pipes, base, score, diagnostics) # draw the screen
    
if __name__ == "__main__":
    main()
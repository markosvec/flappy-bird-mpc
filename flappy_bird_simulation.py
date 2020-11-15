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

pygame.font.init() # initialize fonts

WIN_WIDTH = 500
WIN_HEIGHT = 800

BG_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs","bg.png")))
STAT_FONT = pygame.font.SysFont("comicsans", 50)

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
    pipe_start_position, pipe_end_position = pipe.physical_position()
    pipe_start_top, pipe_start_bottom = pipe_start_position
    pipe_end_top, pipe_end_bottom = pipe_end_position

    # draw straight lines from the bird to the pipe corners
    pygame.draw.line(surface, (0,255,0), bird_position, pipe_start_top, 3)
    pygame.draw.line(surface, (0,255,0), bird_position, pipe_start_bottom ,3)
    pygame.draw.line(surface, (0,255,0), bird_position, pipe_end_top, 3)
    pygame.draw.line(surface, (0,255,0), bird_position, pipe_end_bottom ,3)

    pygame.draw.circle(surface, (255,0,0), (int(bird_position[0]), int(bird_position[1])), int(0.75*bird.IMGS[0].get_height()), 3) # draw a circle around the bird; because of some reason this doesn't accept floats
    pygame.draw.polygon(surface, (255,0,0), [(pipe_start_top[0],0), pipe_start_top, pipe_end_top, (pipe_end_top[0],0)], 3) # draw rectangle around the top pipe
    pygame.draw.polygon(surface, (255,0,0), [(pipe_start_bottom[0],730), pipe_start_bottom, pipe_end_bottom, (pipe_end_bottom[0],730)], 3) # draw rectangle around the bottom pipe

def draw_window(win, bird, pipes, base, score, diagnostics=False):
    win.blit(BG_IMG, (0,0))

    for pipe in pipes:
        pipe.draw(win)

    text = STAT_FONT.render("Score: " + str(score), 1, (255,255,255))
    win.blit(text, (WIN_WIDTH - 10 - text.get_width(), 10))

    base.draw(win)
    bird.draw(win)

    if diagnostics:
        # draw lines from the bird to the pipes
        surface = pygame.display.get_surface()
        draw_diagnostics(surface, bird, pipes)

    pygame.display.update()

def bird_controller(bird, pipe):
    # simple controler obtained with NN

    jump = False 

    bird_y = bird.y
    top_pipe_y  = pipe.height
    bottom_pipe_y = pipe.bottom

    dist_top = abs(bird_y - top_pipe_y)
    dist_bottom = abs(bird_y - bottom_pipe_y)
    output = dist_top - dist_bottom

    if output > 1:
        jump = True

    return jump

def main():

        bird = Bird(230,350)
        base = Base(730)
        pipes = [Pipe(600)]
        win = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
        clock = pygame.time.Clock()

        score = 0

        diagnostics = True
        run = True
        max_iter = 5000
        t = np.arange(max_iter)
        U = np.zeros((max_iter, 1))
        X = np.zeros((max_iter, 1))
        Y = np.zeros((max_iter, 1))
        for i in range(0,max_iter):
            clock.tick(30) # perform iterations every 30ms

            # check whether user requested the game to end
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    quit()

            # check whether the next pipe is pipe0 or pipe1
            if len(pipes) > 1 and bird.x > pipes[0].x + pipes[0].PIPE_TOP.get_width():
                pipe_ind = 1
            else:
                pipe_ind = 0

            jump = bird_controller(bird, pipes[pipe_ind]) # implement the controler obtained by neaural net

            if i == 0:
                X[i] = 0
            else:
                X[i] = X[i-1] + base.VEL
            _, Y[i] = bird.physical_position()

            if jump:
                bird.jump()
                U[i] = 1
            else:
                U[i] = 0

            bird.move() # move the bird
            add_pipe = False
            rem = []
            for pipe in pipes:

                # if bird collided, kill the bird
                if pipe.collide(bird):
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
            if bird.y + bird.img.get_height() >= 730 or bird.y < 0:
                break

            base.move() # move the base
            draw_window(win, bird, pipes, base, score, diagnostics) # draw the screen
        
            print("Iteration: " + str(i))
       
        # write identification experiment data to the file
        with open('identification_data.csv', 'w', newline='') as csvfile:
            fieldnames = ['sample', 'x', 'y','u']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            for i in t:
                writer.writerow({'sample': i, 'x': X[i][0], 'y': Y[i][0], 'u': U[i][0]})
          

        # plot states and input
        _, (ax_x, ax_y, ax_u) = plt.subplots(3)

        ax_x.plot(t, X)
        ax_x.set_ylabel('Traveled distance (px)')
        ax_x.grid()
        ax_x.set_xlim([t[0], t[-1]])

        ax_y.plot(t, Y)
        ax_y.set_ylabel('Vertical position (px)')
        ax_y.grid()
        ax_y.set_xlim([t[0], t[-1]])

        ax_u.plot(t, U, 'tab:red')
        ax_u.set_ylabel('Input signal')
        ax_u.set_xlabel('Iteration number')
        ax_u.grid()
        ax_u.set_xlim([t[0], t[-1]])

        plt.show()
    
if __name__ == "__main__":
    main()
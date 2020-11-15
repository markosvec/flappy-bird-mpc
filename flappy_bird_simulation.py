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
import cvxpy as cp

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
    pygame.draw.line(surface, (0,255,0), (bird_position[0], bird_position[1]), pipe_start_top, 3)
    pygame.draw.line(surface, (0,255,0), (bird_position[0], bird_position[1]), pipe_start_bottom ,3)
    pygame.draw.line(surface, (0,255,0), (bird_position[0], bird_position[1]), pipe_end_top, 3)
    pygame.draw.line(surface, (0,255,0), (bird_position[0], bird_position[1]), pipe_end_bottom ,3)

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

def bird_controller(bird, pipes):

    bird_position = bird.physical_position() # get bird state

    # get pipe position
    pipe = pipe_in_front(bird, pipes)
    pipe_start_position, _ = pipe.physical_position()
    pipe_start_top, pipe_start_bottom = pipe_start_position

    x0 = np.array([bird_position[0], bird_position[1], bird_position[2]])
    N = 2
    n_states = 3

    bigM = 100
    robut_margin = 30

    x = cp.Variable((n_states, N+1))
    u = cp.Variable(N, boolean=True)
    eps = cp.Variable((2,N))
    objective = cp.Minimize(cp.sum(u) + cp.sum_squares(x[1,:] - pipe_start_bottom[1] + robut_margin) + 1e8*cp.sum_squares(eps))

    constraints = []
    for i in range(N):
        constraints += [x[0,i+1] == x[0,i] + 5] # x dynamics
        constraints += [x[1,i+1] == x[1,i] + x[2,i]] # y dynamics
        constraints += [x[2,i+1] + 20 <= bigM*(1-u[i]), -x[2,i+1] - 20 <= bigM*(1-u[i])]
        constraints += [x[2,i+1] - x[2,i] - 2 <= bigM*u[i], -x[2,i+1] + x[2,i] + 2 <= bigM*u[i]]

        constraints += [x[1,i+1] >= 0, x[1,i+1] <= 730] # position of a bird inside the screen
        constraints += [x[1,i+1] <= pipe_start_bottom[1] - robut_margin + eps[0,i], x[1,i+1] >= pipe_start_top[1] + robut_margin - eps[1,i]]
        constraints += [eps[:,i] >= 0]

    constraints += [x[:,0] == x0] # define bird initial state
    prob = cp.Problem(objective, constraints)

    result = prob.solve()
    jump = int(u.value[0])
    
    return jump

def main():

        bird = Bird(230,350)
        base = Base(730)
        pipes = [Pipe(600)]
        win = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
        clock = pygame.time.Clock()

        score = 0
        alive = True

        diagnostics = True
        write_enable = False
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

            jump = bird_controller(bird, pipes) # implement the controler obtained by neaural net

            # save current position data
            if i == 0:
                X[i] = 0
            else:
                X[i] = X[i-1] + base.VEL
            _, Y[i], _ = bird.physical_position()

            # save current input data
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
                    #alive = False
                    #break
                    pass

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
        
            print("Iteration: " + str(i))
       
        # write identification experiment data to the file
        if write_enable:
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
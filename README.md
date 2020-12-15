![Logo](https://gamedot.pl/uploads/media/default/0001/06/thumb_5778_default_newsview.jpeg)

# Flappy Bird MPC
Flappy Bird clone played by a Model Predictive Control (MPC) based algorithm implemented with CVXPY module.

# Instructions
Just flappy_bird_simulation.py and watch MPC playing the game of flappy bird!

# Original version
The original version of the flappy clone was borrowed from [Tech With Tim](https://www.youtube.com/results?search_query=tech+with+tim). The code for the original version can be found here: https://github.com/techwithtim/NEAT-Flappy-Bird. In my version, I tweaked the physics a bit, added some diagnostic visualization and replaced the AI with the MPC.

# Solver
The algorithm uses CVXPY for creating the optimization problem and [Gurobi](https://www.gurobi.com/) for solving it. Therefore, you should [download](https://www.gurobi.com/free-trial/) and install Gurobi. There is a trial version available, while students can get the student version for free. Of course, you can always use some other solver if you have it. Just bear in mind that the problem is nonlinear mixed integer, so your solver should be able to handle those.

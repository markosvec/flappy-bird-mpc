import cvxpy as cp

class Controller:
    BIG_M = 100
    ROBUST_MARGIN = 20

    def __init__(self, N, n_states):
        self.N = N
        self.n_states = n_states
        self.x = cp.Variable((n_states, N+1))
        self.u = cp.Variable(N, boolean=True)
        self.eps = cp.Variable((2,N))
        self.objective = cp.Minimize(0) # initialize cost
        self.constraints = [] # initialize constraints
        self.prob = cp.Problem(self.objective, self.constraints) # initialize problem

    def update(self, x0, limits):

        self.objective = cp.Minimize(cp.sum_squares(self.x[1,:] - limits[0] + self.ROBUST_MARGIN) + 1e8*cp.sum(self.eps))

        self.constraints = []
        for i in range(self.N):
            self.constraints += [self.x[0,i+1] == self.x[0,i] + 5] # x dynamics
            self.constraints += [self.x[1,i+1] == self.x[1,i] + self.x[2,i]] # y dynamics
            self.constraints += [self.x[2,i+1] + 20 <= self.BIG_M*(1-self.u[i]), - self.x[2,i+1] - 20 <= self.BIG_M*(1-self.u[i])]
            self.constraints += [self.x[2,i+1] - self.x[2,i] - 2 <= self.BIG_M*self.u[i], -self.x[2,i+1] + self.x[2,i] + 2 <= self.BIG_M*self.u[i]]

            self.constraints += [self.x[1,i+1] >= 0, self.x[1,i+1] <= 730] # position of a bird inside the screen
            self.constraints += [self.x[1,i+1] <= limits[0] - self.ROBUST_MARGIN + self.eps[0,i], self.x[1,i+1] >= limits[1] + self.ROBUST_MARGIN - self.eps[1,i]]
            self.constraints += [self.eps[:,i] >= 0]

        self.constraints += [self.x[:,0] == x0] # define bird initial state
        self.prob = cp.Problem(self.objective, self.constraints)

    def solve(self):
        _ = self.prob.solve()
        jump = int(self.u.value[0])
        return jump
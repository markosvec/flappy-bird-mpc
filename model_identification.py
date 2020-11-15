import csv
import numpy as np
import matplotlib.pyplot as plt

def identify_matrices(X, Y, U, max_order):

    num_samples = len(X)
    n_states = 2
    n_inputs = 1
    X = np.array(X)
    Y = np.array(Y)
    U = np.array(U)
    states = np.concatenate((X.reshape(1,num_samples),Y.reshape(1,num_samples)) ,axis=0)
    inputs = U.reshape(1,num_samples)

    i = 1
    for order in range(max_order,0,-1):

        if i==1:
            data_prev = states[:,order-1:-1]
            data_next = states[:,order:]
        else:
            data_prev = np.concatenate((data_prev, states[:,order-1:-i]), axis = 0)
            data_next = np.concatenate((data_next, states[:,order:-i+1]), axis=0)
            
        i += 1

    input_curr = inputs[:,max_order-1:-1]
    data_prev = np.concatenate((data_prev, input_curr, np.ones((1, num_samples-max_order))), axis=0)

    M = np.matmul(data_next, np.linalg.pinv(data_prev))

    A = M[:, 0:n_states*max_order]
    B = M[:, n_states*max_order : n_states*max_order + n_inputs] 
    C = M[:, n_states*max_order + n_inputs : n_states*max_order + n_inputs + 1]

    return np.matrix(A), np.matrix(B.reshape(n_states*max_order,1)), np.matrix(C)

def simulate_system(A, B, C, state_0, inputs):

    state_curr = np.matrix(state_0)
    n_states = A.shape[0]
    n_sim = inputs.shape[0]
    
    states = np.zeros((n_states,n_sim+1))
    states[:,0] = np.reshape(np.array(state_curr),n_states)
    for i in range(n_sim):
        state_curr = np.matmul(A,state_curr) + np.matmul(B,np.matrix(inputs[i])) + C
        states[:,i+1] = np.reshape(np.array(state_curr),n_states)

    return states

def simulate_system_simple(state_0, inputs):

    n_sim = inputs.shape[0]

    states = np.zeros((3,n_sim + 1))
    state_curr = state_0
    states[:,0] = state_curr
    for i in range(n_sim):
        x_next = state_curr[0] + 5
        y_next = state_curr[1] + state_curr[2]
        v_next = (state_curr[2] + 2)*(1-inputs[i]) - 20*inputs[i]

        state_curr = np.array([x_next, y_next, v_next])
        states[:,i+1] = state_curr

    return states 

def main():

    t = []
    X = []
    Y = []
    U = []
    with open('identification_data.csv', newline='') as csvfile:
        row_data = csv.reader(csvfile, delimiter=',')
        header = True
        for row in row_data:
            if header:
                header = False
            else:
                t.append(float(row[0]))
                X.append(float(row[1]))
                Y.append(float(row[2]))
                U.append(float(row[3]))

    '''
    order = 2
    n_states = order*2
    A, B, C = identify_matrices(X, Y, U, order)
    # simulate the identified system
    state_0 = np.reshape(np.concatenate((np.array([X[0], Y[0]]), np.zeros((n_states-2)))), (n_states,1))
    inputs = np.array(U)
    states_hat = simulate_system(A, B, C, state_0, inputs)
    '''
    state_0 = np.array([0, Y[0], 0])
    inputs = np.array(U)
    states_hat = simulate_system_simple(state_0, inputs)

    # plot states and input
    _, (ax_x, ax_y, ax_u) = plt.subplots(3)

    ax_x.plot(t, X)
    ax_x.plot(t,states_hat[0,:-1])
    ax_x.set_ylabel('Traveled distance (px)')
    ax_x.grid()
    ax_x.set_xlim([t[0], t[-1]])

    ax_y.plot(t, Y)
    ax_y.plot(t, states_hat[1,1:])
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
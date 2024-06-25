import numpy as np
import pickle

class MarkovChain(object):
    """
    Represents the Markov Chain functionality.
    """
    def __init__(self, transition_matrix, states):
        """
        Initialize the MarkovChain instance.

        Parameters
        ----------
        transition_matrix : 2-D array
            A 2-D array representing the probabilities of change of 
            state in the Markov Chain. Each row of the matrix should 
            sum to 1, and the matrix should be square, meaning its 
            dimensions are [n_states x n_states], where n_states is 
            the number of states in the Markov Chain.

        states : 1-D array
            An array representing the states of the Markov Chain. It
            needs to be in the same order as the transition_matrix. 
            The length of this array should match the dimensions of 
            the transition_matrix, ensuring each state has a 
            corresponding row and column in the matrix.
        """
        # Load transition_matrix from a pickle file
        with open(transition_matrix, 'rb') as f:
            self.transition_matrix = pickle.load(f)
        
        # Load states from a pickle file
        with open(states, 'rb') as f:
            self.states = pickle.load(f)

        # Validation
        if not all(np.isclose(np.sum(self.transition_matrix, axis=1), 1)):
            raise ValueError("Each row in the transition matrix must sum to 1.")
        if len(self.states) != self.transition_matrix.shape[0]:
            raise ValueError("The number of states must match the dimensions of the transition matrix.")

        self.index_dict = {state: index for index, state in enumerate(self.states)}
        self.state_dict = {index: state for index, state in enumerate(self.states)}


    def next_state(self, current_state):
        """
        Returns the state of the random variable at the next time instance.
        """
        return np.random.choice(self.states, p=self.transition_matrix[self.index_dict[current_state], :])

    def next_state_probabilities(self, current_state):
        """
        Returns the probabilities of moving to each possible next state from the current state.
        """
        current_state_index = self.index_dict[current_state]
        probabilities = self.transition_matrix[current_state_index, :]
        return {state: prob for state, prob in zip(self.states, probabilities)}
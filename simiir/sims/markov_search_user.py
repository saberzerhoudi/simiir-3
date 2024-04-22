import numpy as np
import pickle
from user.loggers import Actions
from ifind.search.query import Query

# Global variables for paths
TRANSITION_MATRIX_PATH = '../example_model/known_session_vectors_suss_matrix.data'
STATES_PATH = '../example_model/known_session_vectors_suss_states.data'

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

        self.index_dict = {self.states[index]: index for index in range(len(self.states))}
        self.state_dict = {index: self.states[index] for index in range(len(self.states))}

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


class BasicMarkovUser(object):
    """
    A basic user model that uses a Markov Chain to decide the next action. Stores references to all the required components, and contains the logical workflow for the simulation. 
    """
    def __init__(self, configuration, transition_matrix, states):
        self.__user_context = configuration.user.user_context
        self.__output_controller = configuration.output
        self.__logger = configuration.user.logger
        
        # Initialize the Markov Chain with the transition matrix and states
        self.__markov_chain = MarkovChain(TRANSITION_MATRIX_PATH, STATES_PATH)
        
        self.__has_started = False 
   
    def decide_action(self):
        """
        Decides the next action based on the Markov Chain model.
        """
        if not self.__has_started:
            last_action = 'None'  
            self.__has_started = True
        else:
            last_action = self.__user_context.get_last_action()
            
        if last_action == Actions.END:
            self.__do_stop()
            return
        
        # Log all probabilities from the current state
        probabilities = self.__markov_chain.next_state_probabilities(last_action)
        self.__logger.log_info(f"Probabilities from {last_action}: {probabilities}")

        # Get the next probable action from the Markov Chain
        next_action = self.__markov_chain.next_state(last_action)
        
        # Map the next action to the corresponding method
        action_method = self.__get_action_method(next_action)
        if action_method:
            action_method()
    
    def __get_action_method(self, action):
        """
        Maps an action to the corresponding method.
        """
        action_methods = {
            Actions.QUERY: self.__do_query,
            Actions.SERP: self.__do_serp,
            Actions.SNIPPET: self.__do_snippet,
            Actions.DOC: self.__do_assess_document,
            Actions.MARK: self.__do_mark_document,
            Actions.END: self.__do_stop,
            'None': self.__do_query,  
        }
        return action_methods.get(action, None)
    
    def __do_query(self):
        """
        Called when the simulated user wishes to issue another query.
        This works by calling the search context for the subsequent query text, and is then issued to the search interface by the search context on behalf of the user.
        If no further queries are available, the logger is told of this - and the simulation will then stop at the next iteration.
        """
        # update the query generator with the latest search context.
        self.__query_generator.update_model(self.__user_context)

        # Get a query from the generator.
        query_text = self.__query_generator.get_next_query(self.__user_context)
        
        if query_text:
            self.__user_context.add_issued_query(query_text)  # Can also supply page number and page lengths here.
            self.__logger.log_action(Actions.QUERY, query=query_text)
            self.__output_controller.log_query(query_text)
            
            return True
        
        self.__output_controller.log_info(info_type="OUT_OF_QUERIES")
        # Tells the logger that there are no remaining queries; the logger will then stop the simulation.
        self.__logger.queries_exhausted()
        return False
    
    def __do_serp(self):
        """
        Called when the simulated user wishes to examine a SERP - the "initial glance" - after issuing a query.
        If the SERP has no results, we continue with the next action - otherwise we will always go and look at said SERP.
        """
        if self.__user_context.get_current_results_length() == 0:
            self.__logger.log_action(Actions.SERP, status="EMPTY_SERP")
            return False  # No results present; return False (we don't continue with this SERP)
        
        # Code updates on 2017-09-28 for refactoring.
        # Simplified this portion -- the SERP impression component now only returns a True/False value.
        is_serp_attractive = self.__serp_impression.is_serp_attractive()
        self.__user_context.add_serp_impression(is_serp_attractive)  # Update the search context.
        
        if is_serp_attractive:
            self.__logger.log_action(Actions.SERP, status="EXAMINE_SERP")
        else:
            self.__logger.log_action(Actions.SERP, status="IGNORE_SERP")
        
        return is_serp_attractive
       
    def __do_snippet(self):
        """
        Called when the user needs to make the decision whether to examine a snippet or not.
        The logic within this method supports previous observations of the same document, and whether the text within the snippet appears to be relevant.
        """
        judgment = False
        snippet = self.__user_context.get_current_snippet()
        self.__user_context.increment_serp_position()
        
        if self.__user_context.get_document_observation_count(snippet) > 0:
            # This document has been previously seen; so we ignore it. But the higher the count, cumulated credibility could force us to examine it?
            self.__logger.log_action(Actions.SNIPPET, status="SEEN_PREVIOUSLY", snippet=snippet)
        
        else:
            # This snippet has not been previously seen; check quality of snippet. Does it show some form of relevance?
            # If so, we return True - and if not, we return False, which moves the simulator to the next step.
            
            #print 'snippet', snippet.doc_id, self.__snippet_classifier.is_relevant(snippet)
            
            if self.__snippet_classifier.is_relevant(snippet):
                snippet.judgment = 1
                self.__logger.log_action(Actions.SNIPPET, status="SNIPPET_RELEVANT", snippet=snippet)
                judgment = True
            else:
                snippet.judgment = 0
                self.__logger.log_action(Actions.SNIPPET, status="SNIPPET_NOT_RELEVANT", snippet=snippet)
        
            self.__snippet_classifier.update_model(self.__user_context)
        return judgment
    
    def __do_assess_document(self):
        """
        Called when a document is to be assessed.
        """
        judgment = False
        if self.__user_context.get_last_query():
            document = self.__user_context.get_current_document()
            self.__logger.log_action(Actions.DOC, status="EXAMINING_DOCUMENT", doc_id=document.doc_id)
            
            #print 'document', document.doc_id, self.__document_classifier.is_relevant(document)
            
            if self.__document_classifier.is_relevant(document):
                document.judgment = 1
                #self.__logger.log_action(Actions.MARK, status="CONSIDERED_RELEVANT", doc_id=document.doc_id)
                self.__user_context.add_relevant_document(document)
                judgment = True
            else:
                document.judgment = 0
                self.__user_context.add_irrelevant_document(document)
                #self.__logger.log_action(Actions.MARK, status="CONSIDERED_NOT_RELEVANT", doc_id=document.doc_id)
                judgment = False

            self.__document_classifier.update_model(self.__user_context)
        
        return judgment
    
    def __do_mark_document(self):
        """
        The outcome of marking a document as relevant. At this stage, the user has decided that the document is relevant; hence True can be the only result.
        """
        judgement_message = {0: 'CONSIDERED_NOT_RELEVANT', 1: 'CONSIDERED_RELEVANT'}
        
        document = self.__user_context.get_current_document()
        
        self.__logger.log_action(Actions.MARK, status=judgement_message[document.judgment], doc_id=document.doc_id)
        
        #self.__logger.log_action(Actions.MARK, doc_id=document.doc_id)
        return True
    
    def __do_stop(self):
        """
        Called when the simulation ends.
        """
        self.__logger.log_info("Simulation ended.")
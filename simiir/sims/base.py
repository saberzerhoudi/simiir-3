import os
import pickle
from user.loggers import Actions
from ifind.search.query import Query
import abc

action_to_function_mapping = {
    'QUERY'  : Actions.QUERY,
    'SERP'   : Actions.SERP,
    'SNIPPET': Actions.SNIPPET,
    'DOC'    : Actions.DOC,
    'MARK'   : Actions.MARK,
    'None'           : None
}


class SimulatedBaseUser(object):
    """
    The simulated user. Stores references to all the required components, and contains the logical workflow for the simulation.
    """
    def __init__(self, configuration):
        self._user_context = configuration.user.user_context
        self._output_controller = configuration.output
        self._logger = configuration.user.logger
        self._document_classifier = configuration.user.document_classifier
        self._snippet_classifier = configuration.user.snippet_classifier
        self._query_generator = configuration.user.query_generator
        self._serp_impression = configuration.user.serp_impression
        self._result_stopping_decision_maker = configuration.user.decision_maker
        self._action_value = None  # Response from the previous action method - True or False? (did the user do or not do what they thought?)
    
        """
        This method is central to the whole simulation - it decides which action the user should perform next.
        The workflow implemented should have a structure similar to the following: 
        (1)  User issues query
        (2)  Examine a snippet
        (3*) If the snippet looks at least somewhat relevant, goto (6) else decide whether to goto (1) or (2)
        (4)  Examine document
        (5*) If the document looks to be relevant to the provided topic, goto (6), else decide whether to goto (1) or (2)
        (6)  Mark the document
        (7*) Decide whether to goto (1) or (2)
        This method returns None.
        
        The last_to_next_action_mapping from the last action to the next action
        decides means that after the action is peformed,
        we get a chance to update the log, state, etc.
        before performing the next action
        """
        self.last_to_next_action_mapping = {
            Actions.QUERY  : self._after_query,
            Actions.SERP   : self._after_serp,
            Actions.SNIPPET: self._after_snippet,
            Actions.DOC    : self._after_assess_document,
            Actions.MARK   : self._after_mark,
            None           : self._after_none
        }

        """
        When an action is to be performed, the action_mapping dictionary is
        used to call the appropriate method to perform the action.
        """
        self.action_mapping = {
            Actions.QUERY  : self._do_query,
            Actions.SERP   : self._do_serp,
            Actions.SNIPPET: self._do_snippet,
            Actions.DOC    : self._do_assess_document,
            Actions.MARK   : self._do_mark_document
        }

    def decide_action(self):
        last_action = self._user_context.get_last_action()
        self.last_to_next_action_mapping[last_action]()
    
    def _do_action(self, action):
        # Update the search context to reflect the most recent action.
        # Logging takes place within each method called (e.g. __do_query()) to reflect different values being passed.
        self._user_context.set_action(action)
        # Now call the appropriate method to perform the action.
        self._action_value = self.action_mapping[action]()
    
    def _do_query(self):
        """
        Called when the simulated user wishes to issue another query.
        This works by calling the search context for the subsequent query text, and is then issued to the search interface by the search context on behalf of the user.
        If no further queries are available, the logger is told of this - and the simulation will then stop at the next iteration.
        """
        # raise a not implemented error
        raise NotImplementedError("Method not implemented")
            
    def _do_serp(self):
        """
        Called when the simulated user wishes to examine a SERP - the "initial glance" - after issuing a query.
        If the SERP has no results, we continue with the next action - otherwise we will always go and look at said SERP.
        """
        # raise a not implemented error
        raise NotImplementedError("Method not implemented")
    
    def _do_snippet(self):
        """
        Called when the user needs to make the decision whether to examine a snippet or not.
        The logic within this method supports previous observations of the same document, and whether the text within the snippet appears to be relevant.
        """
        # raise a not implemented error
        raise NotImplementedError("Method not implemented")
    
    def _do_assess_document(self):
        """
        Called when a document is to be assessed.
        """
        # raise a not implemented error
        raise NotImplementedError("Method not implemented")
    
    def _do_mark_document(self):
        """
        The outcome of marking a document as relevant. At this stage, the user has decided that the document is relevant; hence True can be the only result.
        """
        # raise a not implemented error
        raise NotImplementedError("Method not implemented")
        
    def _do_result_stopping_decider(self):
        """
        Method which returns whether a further snippet should be examined, the next query should be issued, or some other action.
        This is the "decision making" logic - and is abstracted to the instantiated DecisionMaker instance to work this out.
        """
        # raise a not implemented error
        raise NotImplementedError("Method not implemented")

    def _after_query(self):
        self._do_action(Actions.SERP)

    def _after_serp(self):
        if self._action_value:
            self._do_action(Actions.SNIPPET)
        else:
            self._do_action(Actions.QUERY)            

    def _after_snippet(self):
        if self._action_value:
            self._do_action(Actions.DOC)
        else:
            self._do_action(self._do_result_stopping_decider())

    def _after_assess_document(self):
        if self._action_value:
            self._do_action(Actions.MARK)
        else:
            self._do_action(self._do_result_stopping_decider())

    def _after_mark(self):
        #This condition will always be True; we won't get here unless the document has been successfully marked!
        #After the document has been marked, the user must decide whether (s)he wants to look at the subsequent snippet, or issue another query.
        self.__do_action(self._do_result_stopping_decider())
    
    def _after_none(self):
        """
        If no action has been supplied from before, then we must be at the start of the search session.
        Therefore, we begin by querying.
        """
        self._do_action(Actions.QUERY)

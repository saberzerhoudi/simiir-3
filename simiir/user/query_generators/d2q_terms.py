from simiir.user.query_generators.base import BaseQueryGenerator
import pandas as pd
from simiir.utils.lm_methods import extract_term_dict_from_text

class D2QQueryGenerator(BaseQueryGenerator):
    """
    Implementing strategies from Engelmann et al. 2023 paper.
    Given a set of seen documents, returns terms (extracted by Doc2Query [Nogueira et al. 2019]) representing these documents.
    https://github.com/terrierteam/pyterrier_doc2query
    """
    def __init__(self, 
                 stopword_file, 
                 background_file=None, 
                 allow_similar=False, 
                 num_samples=4,
                 batch_size=10,
                 device="cuda",
                 verbose=True
                 ):
        
        super().__init__(stopword_file, background_file, allow_similar)
        from pyterrier_doc2query import Doc2Query
        
        import torch

        self.doc2query = Doc2Query(append=False, 
                                   num_samples=num_samples, 
                                   device=torch.device(device), 
                                   batch_size=batch_size, 
                                   verbose=verbose)

    def generate_query_list(self, user_context):

        if user_context.get_all_examined_documents():
            doc_contents = [self._transform_to_doc(item) for item in user_context.get_all_examined_documents()]
            queries = self.doc2query.transform(pd.DataFrame(doc_contents))[['docno', 'querygen']]

            #counts are preserved until here
            queries['querygen'] = queries.querygen.apply(lambda text: extract_term_dict_from_text(text, self._stopword_file))
            
            queries['querygen'] = queries.querygen.apply(lambda term_dict: {term: self._get_idf(term, user_context) for term in term_dict.keys() if self._get_idf(term, user_context) < 0.5})

            #idfs are preserved until here
            terms = {k: v for d in queries['querygen'].to_list() for k, v in d.items()}
            
            first_query = user_context._issued_queries[0].terms

            query_list = [(f"{first_query} {term}", 0) for term in terms.keys()]
            return query_list 


        else:
            #first where the first query is issued
            query_list = super().generate_query_list(user_context)
            return query_list

    def _transform_to_doc(self, item):
        return {"docno" : item.doc_id, "text" : item.content}
    
    def _get_idf(self, term, user_context):
        #ugly way of getting the index
        index = user_context._search_interface._PyTerrierSearchInterface__engine._Terrier__index

        lex = index.getLexicon()
        df_term = lex[term].getDocumentFrequency() if term in lex else 0.5
        return 1/df_term

    def get_next_query(self, user_context):
        
        self._query_list = self.generate_query_list(user_context)

        next_query = super().get_next_query(user_context)

        return next_query
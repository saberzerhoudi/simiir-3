from simiir.search_interfaces.base_interface import BaseSearchInterface
import logging

log = logging.getLogger('simuser.search_interfaces.pyterrier_interface')

class PyTerrierSearchInterface(BaseSearchInterface):
    def __init__(self, 
                 dataset : str, 
                 wmodel : str = None, 
                 controls : dict = None, 
                 properties : dict = None, 
                 variant : str = 'terrier_stemmed_text', 
                 text_field : str = 'body', 
                 memory=False
                 ):
        super().__init__()
        import pyterrier as pt
        if not pt.started():
            pt.init()

        self.__index = pt.IndexFactory.of(pt.get_dataset(dataset).get_index(variant=variant), memory=memory)
        self.__reader = self.__index.getMetaIndex()

        if self.__reader is None: log.warning("No reader defined, cannot fetch document text, doing so will result in an error")
        for k in ['docno', text_field]:
            if k not in self.__reader.getKeys():
                log.warning(f"Essential MetaData {k} not found in reader, cannot fetch document text, doing so will result in an error")
                self.__reader = None
        
        if wmodel is not None: self.__engine = pt.BatchRetrieve(self.__index, wmodel, controls=controls, properties=properties)
        else: self.__engine = None
    
    def issue_query(self, query, top=100):
        assert self.__engine is not None, "No engine defined"
        response = self.__engine.search(query)
        response = [*response.groupby('qid').head(top).rename(columns={'qid':'query_id', 'docid':'document_id', 'score':'document_score'})['query_id', 'document_id', 'score', 'rank'].itertuples(index=False)]
    
        self._last_query = query
        self._last_response = response
        return response

    def get_document(self, document_id):
        assert self.__reader is not None, "No reader defined"
        return self.__reader.getDocument("docno", document_id)
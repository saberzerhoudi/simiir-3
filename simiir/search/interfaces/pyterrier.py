from simiir.search.interfaces.base import BaseSearchInterface
from simiir.search.interfaces import Document
import logging

log = logging.getLogger('simuser.search.interfaces.pyterrier')

class PyTerrierSearchInterface(BaseSearchInterface):
    """
    Interface for using PyTerrier for BatchRetrieval or Meta Index access

    Parameters:
    index_or_dir : str
        Reference to PyTerrier Index
    wmodel : str
        Reference to PyTerrier weighting model
    controls : dict
        Controls for the weighting model
    properties : dict
        Properties for the weighting model
    text_field : str
        Field in the index to use as the text field
    memory : bool
        Whether to load the index into memory
    """
    def __init__(self, 
                 index_or_dir : str, 
                 wmodel : str = None, 
                 controls : dict = None, 
                 properties : dict = None, 
                 text_field : str = 'body', 
                 memory : bool = False,
                 ):
        super().__init__()
        import pyterrier as pt
        if not pt.started():
            pt.init()

        self.__index = pt.IndexFactory.of(index_or_dir, memory=memory)
        self.__reader = self.__index.getMetaIndex()

        if self.__reader is None: log.warning("No reader defined, cannot fetch document text, doing so will result in an error")
        for k in ['docno', text_field]:
            if k not in self.__reader.getKeys():
                log.warning(f"Essential MetaData {k} not found in reader, cannot fetch document text, doing so will result in an error")
                self.__reader = None
        
        if wmodel is not None: self.__engine = pt.BatchRetrieve(self.__index, wmodel, controls=controls, properties=properties)
        else: self.__engine = None

    @classmethod
    def from_dataset(cls, 
                     dataset : str, 
                     variant : str = 'terrier_stemmed_text', 
                     wmodel : str = None, 
                     controls : dict = None, 
                     properties : dict = None, 
                     text_field : str = 'body', 
                     memory : bool = False):
        import pyterrier as pt
        if not pt.started():
            pt.init()
        index_ref = pt.get_dataset(dataset).get_index(variant=variant)
        return cls(index_ref, wmodel=wmodel, controls=controls, properties=properties, text_field=text_field, memory=memory)
    
    def issue_query(self, query, top=100):
        assert self.__engine is not None, "No engine defined"
        response = self.__engine.search(query)
        response = [*response.groupby('qid').head(top).rename(columns={'qid':'query_id', 'score':'score'})['query_id', 'docid', 'score', 'rank'].itertuples(index=False)]
    
        self._last_query = query
        self._last_response = response
        return response

    def get_document(self, document_id):
        assert self.__reader is not None, "No reader defined"
        content =  self.__reader.getDocument("docno", document_id)
        return Document(id=document_id, content=content, doc_id=document_id)
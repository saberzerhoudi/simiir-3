from simiir.search.interfaces.base import BaseSearchInterface
from simiir.search.interfaces import Document
from ifind.search.engines.terrier import Terrier
from typing import Any, Optional, Union
import logging

log = logging.getLogger('simuser.search.interfaces.pyterrier')

class PyTerrierSearchInterface(BaseSearchInterface):
    """
    Interface for using PyTerrier for BatchRetrieval or Meta Index access

    Parameters:
    index_or_dir : Union[str, Any]
        Reference to PyTerrier Index
    pipeline : Any
        Reference to pre-built PyTerrier pipeline
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
                 index_or_dir : Union[str, Any], 
                 pipeline : Optional[Any] = None,
                 wmodel : Optional[str] = None, 
                 controls : Optional[dict] = None, 
                 properties : Optional[dict] = None, 
                 text_field : Optional[str] = 'body', 
                 memory : Optional[bool] = False,
                 ):
        super().__init__()
        import pyterrier as pt
        if not pt.started():
            pt.init()

        self.__engine = Terrier(index_ref=index_or_dir, 
                                wmodel=wmodel, 
                                controls=controls, 
                                properties=properties, 
                                text_field=text_field,
                                pipeline=pipeline,
                                memory=memory)


    def issue_query(self, query, top=100):
        assert self.__engine is not None, "No engine defined"
        query.top = top
        response = self.__engine.search(query)

        self._last_query = query
        self._last_response = response
        return response

    def get_document(self, document_id):
        assert self.__engine.__reader is not None, "No reader defined"
        content =  self.__engine.__reader.getDocument("docno", document_id)
        return Document(id=document_id, content=content, doc_id=document_id)
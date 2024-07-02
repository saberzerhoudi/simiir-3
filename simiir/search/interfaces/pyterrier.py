from simiir.search.interfaces.base import BaseSearchInterface
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
    dataset : str
        PyTerrier dataset with pre-built index
    variant : str
        Variant of the dataset index to use
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
                 index_or_dir : Optional[Union[str, Any]] = None, 
                 dataset : Optional[str] = None,
                 variant : Optional[str] = 'terrier_stemmed_text',
                 pipeline : Optional[Any] = None,
                 wmodel : Optional[str] = None, 
                 controls : Optional[dict] = None, 
                 properties : Optional[dict] = None, 
                 text_field : Optional[str] = 'body', 
                 memory : Optional[bool] = False,
                 ):
        assert index_or_dir is not None or dataset is not None, "No index or dataset defined"
        super().__init__()
        self.__engine = Terrier(index_ref=index_or_dir, 
                                dataset=dataset,
                                variant=variant,
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
        return self.__engine.get_document(document_id)
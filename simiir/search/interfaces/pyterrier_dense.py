from simiir.search.interfaces.pyterrier import PyTerrierInterface
from typing import Union, Any

class PyTerrierDenseInterface(PyTerrierInterface):
    """
    Interface for using a Dense Retrieval model with PyTerrier

    Parameters:
    index_or_dir : str or Any
        Reference to PyTerrier FlexIndex
    model_name_or_path : str
        Reference to AutoModel HuggingFace compatible model or path to model
    meta_index : str or Any
        Reference to PyTerrier Index
    index_text_field : str
        Field in the index to use as the text field
    memory : bool
        Whether to load the index into memory
    batch_size : int
        Batch size for the model
    text_field : str
        Field for the model to use as the text field
    verbose : bool
        Whether to output verbose logging
    device : None
        Device to use for the model
    """
    def __init__(self, 
                 index_or_dir : Union[str, Any], 
                 model_name_or_path : str, 
                 meta_index : Union[str, Any], 
                 index_text_field : str = 'body', 
                 memory=False, 
                 batch_size=32, 
                 text_field='text', 
                 verbose=False, 
                 device=None 
                 ):
        super().__init__(meta_index, text_field=index_text_field, memory=memory)
        from pyterrier_dr import HgfBiEncoder
        if isinstance(index_or_dir, str):
            from pyterrier_dr import NumpyIndex 
            index = NumpyIndex(index_or_dir)
        else: index = index_or_dir

        model = HgfBiEncoder.from_pretrained(model_name_or_path, batch_size=batch_size, text_field=text_field, verbose=verbose, device=device)
        self.__engine = model >> index % 1000
    
    @classmethod
    def from_dataset(cls, 
                     index_or_dir : Union[str, Any], 
                     model_name_or_path : str, 
                     dataset : str, # Pyterrier dataset with pre-built index
                     variant : str = 'terrier_stemmed_text', # Variant of the dataset index to use
                     meta_index_text_field : str = 'text', 
                     memory=False, 
                     batch_size=32, 
                     text_field='text', 
                     verbose=False, 
                     device=None):
        import pyterrier as pt
        if not pt.started():
            pt.init()
        meta_index_ref = pt.get_dataset(dataset).get_index(variant=variant)
        return cls(index_or_dir, model_name_or_path, meta_index_ref, index_text_field=meta_index_text_field, memory=memory, batch_size=batch_size, text_field=text_field, verbose=verbose, device=device)

class PyterrierReRankerInterface(PyTerrierInterface):
    """
    Interface for using a Dense Retrieval model with PyTerrier for re-ranking

    Parameters:
    model_name_or_path : str
        Reference to AutoModel HuggingFace compatible model or path to model
    meta_index : str or Any
        Reference to PyTerrier Index
    wmodel : str
        Weighting model to use
    controls : dict
        Controls for the weighting model
    properties : dict
        Properties for the weighting model
    index_text_field : str
        Field in the index to use as the text field
    memory : bool
        Whether to load the index into memory
    batch_size : int
        Batch size for the model
    text_field : str
        Field for the model to use as the text field
    verbose : bool
        Whether to output verbose logging
    device : None
        Device to use for the model
    rerank_depth : int
        Depth to re-rank to
    """
    def __init__(self, 
                 model_name_or_path : str, 
                 meta_index : str, 
                 wmodel : str = 'BM25',
                 controls : dict = None,
                 properties : dict = None,
                 index_text_field : str = 'body', 
                 memory=False, 
                 batch_size=32, 
                 text_field='text', 
                 verbose=False, 
                 device=None,
                 rerank_depth : int = 100
                 ):
        super().__init__(meta_index, wmodel=wmodel, controls=controls, properties=properties, text_field=index_text_field, memory=memory)
        import pyterrier as pt
        if not pt.started():
            pt.init()
        from pyterrier_dr import HgfBiEncoder

        model = HgfBiEncoder.from_pretrained(model_name_or_path, batch_size=batch_size, text_field=text_field, verbose=verbose, device=device)
        self.__engine = self.__engine % rerank_depth >> pt.text.get_text(self.__index, index_text_field) >> model

    @classmethod
    def from_dataset(cls, 
                     model_name_or_path : str, 
                     dataset : str, 
                     variant : str = 'terrier_stemmed_text', 
                     wmodel : str = 'BM25',
                     controls : dict = None,
                     properties : dict = None,
                     meta_index_text_field : str = 'text', 
                     memory=False, 
                     batch_size=32, 
                     text_field='text', 
                     verbose=False, 
                     device=None):
        import pyterrier as pt
        if not pt.started():
            pt.init()
        meta_index_ref = pt.get_dataset(dataset).get_index(variant=variant)
        return cls(model_name_or_path, 
                   meta_index_ref, 
                   wmodel=wmodel, 
                   controls=controls, 
                   properties=properties, 
                   index_text_field=meta_index_text_field, 
                   memory=memory, 
                   batch_size=batch_size, 
                   text_field=text_field, 
                   verbose=verbose, 
                   device=device)
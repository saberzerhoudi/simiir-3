from simiir.search_interfaces.pyterrier_interface import PyTerrierInterface
from typing import Union, Any

class PyTerrierDenseInterface(PyTerrierInterface):
    def __init__(self, 
                 index_or_dir : Union[str, Any], 
                 model_name_or_path : str, 
                 dataset : str, 
                 variant : str = 'terrier_stemmed_text', 
                 index_text_field : str = 'body', 
                 memory=False, 
                 batch_size=32, 
                 text_field='text', 
                 verbose=False, 
                 device=None
                 ):
        super().__init__(dataset, variant=variant, text_field=index_text_field, memory=memory)
        from pyterrier_dr import HgfBiEncoder

        if isinstance(index_or_dir, str):
            from pyterrier_dr import NumpyIndex 
            index = NumpyIndex(index_or_dir)
        else: index = index_or_dir

        model = HgfBiEncoder.from_pretrained(model_name_or_path, batch_size=batch_size, text_field=text_field, verbose=verbose, device=device)
        self.__engine = model >> index % 1000

class PyterrierReRankerInterface(PyTerrierInterface):
    def __init__(self, 
                 model_name_or_path : str, 
                 dataset : str, 
                 variant : str = 'terrier_stemmed_text', 
                 index_text_field : str = 'text', 
                 wmodel = 'BM25',
                 controls : dict = None,
                 properties : dict = None,
                 memory=False, 
                 rerank_depth : int = 100,
                 batch_size=32, 
                 text_field='text', 
                 verbose=False, 
                 device=None):
        super().__init__(dataset, wmodel=wmodel, controls=controls, properties=properties, variant=variant, text_field=index_text_field, memory=memory)
        import pyterrier as pt
        if not pt.started():
            pt.init()
        from pyterrier_dr import HgfBiEncoder

        model = HgfBiEncoder.from_pretrained(model_name_or_path, batch_size=batch_size, text_field=text_field, verbose=verbose, device=device)
        self.__engine = self.__engine % rerank_depth >> pt.text.get_text(self.__index, index_text_field) >> model
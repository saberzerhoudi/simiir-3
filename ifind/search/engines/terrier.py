from typing import Any, Union
import logging
from ifind.search.engine import Engine
from ifind.search.response import Response
from ifind.search.exceptions import EngineConnectionException

log = logging.getLogger('ifind.search.engines.terrier')

class Terrier(Engine):
    def __init__(self, 
                 index_ref : Union[str, Any] = '',
                 wmodel : str = None,
                 controls : dict = None,
                 properties : dict = None,
                 memory : bool = False,
                 **kwargs):
        Engine.__init__(self, **kwargs)
        import pyterrier as pt
        if not pt.started():
            pt.init()
        self.index_ref = str(index_ref)
        try:
            self.__index = pt.IndexFactory.of(index_ref, memory=memory)
        except Exception as e:
            msg = "Could not open Terrier index from: " + str(index_ref)
            raise EngineConnectionException(self.name, msg)
        self.__reader = self.__index.getMetaIndex()
        self.__engine = pt.BatchRetrieve(self.__index, wmodel=wmodel, controls=controls, properties=properties) if wmodel else None 
    
    def set_engine(self, engine : Any):
        import pyterrier as pt
        if not pt.started():
            pt.init()
        assert issubclass(pt.Transformer, engine), "Engine must be a PyTerrier Transformer."
        self.__engine = engine
    
    def set_wmodel(self, wmodel : str, controls : dict = None, properties : dict = None):
        import pyterrier as pt
        if not pt.started():
            pt.init()
        self.__engine = pt.BatchRetrieve(self.__index, wmodel=wmodel, controls=controls, properties=properties)

    def __parse_query_terms(self, query):
        if not query.top:
            query.top = 10

        if query.top < 1:
            query.top = 10
    
    @staticmethod
    def _parse_terrier_response(response):
        output = Response(response.query.iloc[0])
        for i in range(len(response)):
            row = response.iloc[i]
            title = getattr(row, 'title', "Untitled")
            url = getattr(row, 'url', row.docno)
            content = getattr(row, 'text', None) 
            rank = row.rank + 1
            docid = row.docno 
            score = row.score
            source = row.source
            response.add_result(title=title, 
                                url=url, 
                                content=content,
                                rank=rank, 
                                docid=docid, 
                                score=score,
                                source=source)
        
        output.result_total = len(response)
        return output
    
    def _request(self, query):
        response = None
        pagelen = query.top
        if self.__engine:
            response = self.__engine.transform(query.terms)
            response = response.sort_values('score', ascending=False).head(pagelen)
            response['source'] = self.index_ref
            if self.__reader:
                response['text'] = response['docno'].apply(lambda x: self.__reader.getDocument('docno', x))
            response = self._parse_terrier_response(response)
        return response

    def _search(self, query):
        """
        Concrete method of Engine's interface method 'search'.
        Performs a search and retrieves the results as an ifind Response.

        Args:
            query (ifind Query): object encapsulating details of a search query.

        Query Kwargs:
            top (int): specifies maximum amount of results to return, no minimum guarantee

        Returns:
            ifind Response: object encapulsating a search request's results.

        Raises:
            EngineException

        Usage:
            Private method.

        """
        self.__parse_query_terms(query)

        return self._request(query)


        
      
from langchain_openai import ChatOpenAI
from langchain_community.chat_models import ChatOllama, ChatAnthropic, ChatVertexAI, ChatCohere
from langchain_core.prompts import PromptTemplate

from tenacity import retry,wait_exponential,stop_after_attempt

import logging
log = logging.getLogger('user.utils.LangChainWrapper')

class LangChainWrapper(object):
   def __init__(self,prompt,provider="ollama",model="mistral",temperature=0.0,verbose=False):
      provider = provider.lower()
      if provider == 'openai':
            self._llm = ChatOpenAI(model=model,temperature=temperature,verbose=verbose)
      elif provider == 'ollama':
         self._llm = ChatOllama(model=model,temperature=temperature,verbose=verbose)
      elif provider == 'anthropic':
         self._llm = ChatAnthropic(model=model,temperature=temperature,verbose=verbose)
      elif provider == 'vertexai':
         self._llm = ChatVertexAI(model=model,temperature=temperature,verbose=verbose)
      elif provider == 'cohere':
         self._llm = ChatCohere(model=model,temperature=temperature,verbose=verbose)
      else:
         raise Exception("Unknown provider to LangChainWrapper")
         
      self._prompt = prompt
      self._chain = self._prompt | self._llm

   @retry(wait=wait_exponential(multiplier=1,min=1,max=5),stop=stop_after_attempt(10))
   def generate_response(self,output_parser,params):
      full_chain = self._chain | output_parser
      valid = False
      out = full_chain.invoke(params)
      log.debug("Initial output: {0}".format(out))
      fields = out.__fields__
      while not valid:
         valid = True
         for attr in fields:
            if not hasattr(out,attr) or fields[attr].annotation != type(getattr(out,attr)):
               new_prompt = """You did not format your response correctly for the request: \n ```{0}``` \n\nYou responded with {1}. Reformat your response to the requested format.""".format(self._prompt.template,out)
               new_template = PromptTemplate(
                  template=new_prompt,
                  input_variables=self._prompt.input_variables,
                  partial_variables=self._prompt.partial_variables,
               )
               chain = new_template | self._llm | output_parser
               out = chain.invoke(params)  
               log.debug("Retried output: {0}".format(out))
               valid = False
               break
      return out


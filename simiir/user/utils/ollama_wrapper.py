
from langchain_openai import ChatOpenAI
from langchain_community.chat_models import ChatOllama
from langchain_core.prompts import PromptTemplate

from tenacity import retry,wait_exponential,stop_after_attempt

class OllamaWrapper(object):
   def __init__(self,prompt,model="mistral",verbose=False):
      if model.lower() == 'openai':
         self._llm = ChatOpenAI(temperature=0.0,verbose=verbose)
      else:
         self._llm = ChatOllama(model=model,temperature=0.0,verbose=verbose)
      self._prompt = prompt
      self._chain = self._prompt | self._llm

   @retry(wait=wait_exponential(multiplier=1,min=1,max=5),stop=stop_after_attempt(10))
   def generate_response(self,output_parser,params):
      full_chain = self._chain | output_parser
      valid = False
      out = full_chain.invoke(params)
      fields = out.__fields__
      while not valid:
         valid = True
         for attr in fields:
            if not hasattr(out,attr) or fields[attr].annotation != type(getattr(out,attr)):
               new_prompt = """You did not format your response correctly to the following: \n ```{0}``` You responded with {1}. Please try again and respond with the correct format.""".format(prompt.template,out)
               new_template = PromptTemplate(
                  template=new_prompt,
                  input_variables=self._prompt.input_variables,
                  partial_variables=self._prompt.partial_variables,
               )
               chain = new_template | self._llm | output_parser
               out = chain.invoke(params)  
               valid = False
               break
      return out


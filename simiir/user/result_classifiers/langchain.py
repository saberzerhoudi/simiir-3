from simiir.user.result_classifiers.base import BaseTextClassifier
from simiir.user.utils.langchain_wrapper import LangChainWrapper
from simiir.utils.tidy import clean_html
from langchain_core.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

import logging
log = logging.getLogger('result_classifier.LangChainTextClassifier')

class SnippetResponse(BaseModel):
    topic: bool = Field("Is the result about the subject matter in the topic description? Answer True if about the topic in the description, else False")
    click: bool = Field("Is it worth clicking on this result to inspect the document? Answer True if it is worth clicking, else False.")

class DocumentResponse(BaseModel):
    topic: bool = Field("Is the document about the subject matter in the topic description? Answer True if about the topic in the description, else False.")
    relevant: bool = Field("Is the document relevant to the topic description? Answer True if relevant, False if not relevant or unknown.")
    explain: str = Field("Summarize the information from the document that is relevant to the topic description and the criteria. Be specific and succint but mention all relevant entities.")

result_type_dict = { "SnippetResponse":SnippetResponse, "DocumentResponse":DocumentResponse}

class LangChainTextClassifier(BaseTextClassifier):
    """

    """
    def __init__(self, topic, user_context, prompt_file, result_type_str, provider = 'ollama', model = 'mistral', temperature = 0.0, verbose = False):
        """

        """
        super(LangChainTextClassifier, self).__init__(topic, user_context)
        self.updating = False
        prompt_template = ""
        with open(prompt_file,'r') as prompt:
            prompt_template = prompt.read()
        self._template = prompt_template + """\n\n{format_instructions}\n"""
        log.debug(self._template)
        result_type = result_type_dict[result_type_str]
        self._output_parser = PydanticOutputParser(pydantic_object=result_type)

        format_instructions = self._output_parser.get_format_instructions()
        log.debug(format_instructions)
        self._prompt = PromptTemplate(
            template=self._template,
            input_variables=["topic_title", "topic_description", "doc_title", "doc_content"],
            partial_variables={"format_instructions": format_instructions})
        
        self._llm = LangChainWrapper(self._prompt, provider, model, temperature, verbose)

    def is_relevant(self, document):
        """
        """

        doc_title = " ".join(clean_html(document.title))
        doc_content = " ".join(clean_html(document.content))
        topic_title = self._topic.title
        topic_description  = self._topic.content

        log.debug(self._prompt.format(topic_title=topic_title, topic_description=topic_description, doc_title=doc_title, doc_content=doc_content))    
        out =self._llm.generate_response(self._output_parser,{ 'topic_title': topic_title, 'topic_description': topic_description, 'doc_title': doc_title, 'doc_content': doc_content })
        log.debug(out)
        return out.click

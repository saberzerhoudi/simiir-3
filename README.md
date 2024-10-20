# SimIIR 3

SimIIR 3 is based on the Python-based SimIIR framework for simulating interactive information retrieval (IIR) that was originally released by Leif Azzopardi and David Maxwell [https://github.com/leifos/simiir] and extended by Zerhoudi et al. [https://github.com/padas-lab-de/simiir-2]. 

The class and package structure of SimIIR 3 has been significantly revised -- and means that SimIIR 3 is not backwards compatiable with the previous version (directly). However, any additional components can be easily ported to the SimIIR 3. 

The reason for updated the packages was to create a cleaner and clearer separation between the different core components within the framework and to enable the development of new simulations (e.g. conversational simulations).


## Framework Architecture

- sims: contains the components for constructing simulations given a configuration, and a flow chart based model of how a simulated user interacts with the search system.
    - search_user:
        - `SimulatedUser`: simulates the complex searcher model workflow
        - Users to be added TODO(@zaber):`MarkovSearchSimulatedUser` and TODO(@leifos):`ConversationalSearchSimulatedUser` 
- user: contains the components for building a simulated user.
    - contexts: 
        - `Memory`: provides a container for storing what actions, etc the user performed during their interaction with the search system. It represents their internal state, knowledge of the world, etc.
        - `Cognitive State`: allows for the modelling of the potential impact of users' cognitive states (e.g., certainty level and sentiment), in addition to the long-term memory effect, on (conversational) search interactions. 
    - loggers:
        - `Action`: the current set of actions: 'QUERY', 'SERP', 'SNIPPET', 'DOC', 'MARK'
        - `BaseLogger`, `FixedCostLogger`, etc: provider a mechanism for logging user actions, recording their costs, and goals, and checking whether the user is finished. 
    - query_generators:
        - `BaseQueryGenerator` has two abstract methods: (1) generate queries, and (2) select next query. For example:
        - `PredeterminedQueryGenerator` takes a list of pre-defined queries read in from file.     
        - `SingleTermQueryGenerator` generates a list of single term queries given the `Topic`.
        - `TrecTopicQueryGenerator` generates a list contain one query, the title of the trec `Topic`.
        -  and many more. 
    - result_classifiers:
        - `BaseTextClassifier` has one asbtract method: (1) is_relevant() which decides if a `Document` is relevant or not to the users information need `Topic`, given their context `Memory`. For example,
        - `PerfectTrecTextClassifier` has knowledge of what is relevant and what is not, given TREC qrels, and returns the perfect decision.
        - `StochasticInformedTrecTextClassifier` has knowledge of what is relevant and what is not, given TREC qrels, but returns an imperfect decision based on the probability of a user judging the document relevant given its relevance label.
        - and many more.
    - result_stopping_decider:
        - `BaseDecisionMaker` has one abstract method to implement `decide()` which returns an `Action` so could be used for any decision within the workflow of a simulated user -- but currently we are using this for making stopping decisions given a users interaction with a list of results. For example:
        - `TotalNonrelDecisionMaker` it will decide to go look at the next snippet, if the number of non relevant items seen has not been exceed, otherwise it will query.
        - `RBPDecisionMaker` it will decide to look at the next snippet with probability rho, otherwise it will query.
        - and many more.

    - serp_impressions:
        - `BaseSERPImpression` has one abstract method to implement `is_serp_attractive()` which returns True if the user thinks the serp is attractive enough to examine, otherwise, False.
        - `StochasticSERPImpression` returns True given some probability of continuing if the patch is good or poor, else False.
        - and more.



![The architecture of our extended SimIIR framework, with the components split across both simulation and user categories. Simulation components define the simulation — a representation of some real‐world user study, with user components defining the behavior of simulated users.](https://github.com/padre-lab-eu/extended-simiir/blob/main/simiir2.png)

## Installation

Add the ifind and SimIIR library to your PYTHONPATH.

To evaluate the effectiveness of the simulated sessions, you will need to download trec_eval [http://trec.nist.gov/trec_eval/].

Add trec_eval to your PATH.

    #### ifind and SimIIR
    export PYTHONPATH="${PYTHONPATH}:/pathTo/ifind:/pathTo/simiir"

    #### trec_user
    export PATH="/pathTo/trec_eval-9.0.7:$PATH"

Create a virtual environment with the packages in requirements.txt (this is the same as the one for ifind).

## Dataset

SimIIR simulate user search session using only a list of five major actions: QUERY (i.e., formulating a query), SERP (i.e., viewing the search result page), SNIPPET (i.e., viewing the document’s metadata), DOC (i.e., viewing the full document’s content) and MARK (i.e., marking the document as relevant or not). We therefore cluster SUSS’s list of actions and pages into broader groups to match the actions we have available in SimIIR (e.g., "QUERY"
action in SimIIR represents the group of actions "issue a first query", "reformulate a query" and "click query suggestion" in SUSS) and remove the non-search related actions (e.g., visiting the home page).

However, any other user behavior dataset can be used to analyze search session logs and extract user-types models following the same method.

## Example of experiments

Create a directory called output in example_sims

cd into the simiir directory, and run:

    python run_simiir.py ../example_sims/trec_bm25_simulation.xml

or

    python run_simiir.py ../example_sims/trec_pl2_simulation.xml

You will see the simulations running where the simulated users use either BM25 or PL2.

The output of the simulations will be in example_sims/output.


## Configuration via simulation.xml files

A simulation requires four main elements: output, topics, users, and a search interface.

### output
This is where the output of the simulation is to be stored.
If you do not want to use trec_eval, set trec_eval to false and it will not automatically evaluate the output of the simulations.


### topics
A set of sample topics have been included in example_data/topics.
You can include each topic that you would like the simulated users to undertake.


### users

A user configuration file contains several parameters that describe user search behavior:
* **queryGenerator** allows to define which strategy the user is adapting to generate his/her queries. 
* **textClassifiers** denotes the method used to assess a document/snippet for relevance. 
* **stoppingDecisionMaker** defines the stopping decision point at which the user stops interacting with the SERP. 
* **logger** denotes the amount of time required for the user to interact with the system. 
* **UserContext** keeps track of all the user's interaction with the system. 
* **serpImpression** is responsible for determining whether the presented SERP is relevant enough to enter and examine in more detail.

A set of sample users have been created and included in example_sims/users.

You can include however many users you would like to use the searchInterface for the specified topics.

Each of the users have been configured differently to show how the different components can be set to instantiate different simulated users.

    #### trec_user
    Submits one query, the topic title.

    Examines each snippet and each document, and considers them relevant.

    #### fixed_depth_user

    Submits three word queries -- generated from the topic description

    Examines to a fixed depth, initially set to 10.

    For each snippet that the fixed_depth_user examines, it stochastically decides whether it should examine the document or not based on the specified probabilities.

    For each document that the fixed_depth_user examines, it stochastically decides whether it should mark it as relevant or not based on the specified probabilities.


### search interface
The search interface is a programmatic representation of the search interface an actual user would use.

It currently lets the simulated user do two actions: query and examine a document.

Note: the simulator acts as a broker to query and fetch documents, and controls the flow of actions (i.e., querying, examining snippets, assessing documents, marking documents as relevant).

So far, one search interface is specified which connects to a Whoosh-based index of TREC documents.



## Contributing to the Framework
Steps for contributing to the framework:

0. Inform the ACM SIGIR #simiir group channel, that you are wanting / proposing a change. Get feedbacks.
1. Raise an issue for the minimum viable addition/change. (i.e., new stopping strategy, or new query generator)
2. Make a branch from main.
3. Follow the naming conventions, etc., and make your changes.
4. Test your changes to ensure that the existing simulations works, and that your proposed change works.
5. Add a simulated user and simuluation that uses your simulated user with your change/extension, that works on the example index.
6. If your change is based on publised work, add your reference to `references.bib`.
7. Make a pull request, and inform the ACM SIGIR #simiir group.










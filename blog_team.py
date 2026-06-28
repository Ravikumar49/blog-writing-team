import operator
from typing import TypedDict
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver


load_dotenv()

# Define the shared state that all agents read from and write to
class BlogState(TypedDict):
    topic: str
    research: str
    fact_check: str
    draft: str
    next_step: str

llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")
search_tool = DuckDuckGoSearchRun()


def researcher(state: BlogState) -> dict:
    # Get the topic from shared state
    topic = state["topic"]
    # Search the web for information on the topic
    search_results = search_tool.invoke(topic)

    # Use the LLM to synthesize raw search results into structured notes
    response = llm.invoke([
        SystemMessage(content=(
            "You are a research specialist. Analyze the search results and "
            "produce structured research notes with key facts, statistics, "
            "and insights. Organize by subtopic with bullet points."
        )),
        HumanMessage(content=(
            f"Research topic: {topic}\n\n"
            f"Search results:\n{search_results}"
        ))
    ])
    # Extract the clean text before saving it to the state
    if isinstance(response.content, list):
        clean_text = response.content[0]["text"]
    else:
        clean_text = response.content
    # Return updated state with the research field populated
    return {"research": clean_text}

def fact_checker(state: BlogState) -> dict:
    research = state["research"]

    response = llm.invoke([
        SystemMessage(content=(
            "You are a fact-checker. Review the research notes below. "
            "Identify the 3-5 most important factual claims. "
            "For each claim, search the web to verify it."
        )),
        HumanMessage(content=f"Research to verify:\n{research}")
    ])

    if isinstance(response.content, list):
        claims = response.content[0]["text"]
    else:
        claims = response.content

    # 1. Split the LLM's text block into individual lines
    claim_lines = [line.strip() for line in claims.split('\n') if line.strip()]
    
    # 2. Create a list to hold all our separate search results
    all_search_results = []
    
    # 3. Loop through each claim and search for it specifically!
    for claim in claim_lines:
        try:
            # We use the actual claim text to query DuckDuckGo
            result = search_tool.invoke(f"Is this true: {claim}")
            all_search_results.append(f"Result for '{claim[:30]}...': {result}")
        except Exception as e:
            all_search_results.append(f"Search failed for '{claim[:30]}...'")
            
    # 4. Combine all the gathered evidence into one massive string
    verification_results = "\n\n".join(all_search_results)

    verification = llm.invoke([
        SystemMessage(content=(
            "You are a fact-checker. Compare the claims against the search "
            "results. For each claim, mark it as VERIFIED, UNVERIFIED, or "
            "NEEDS CORRECTION. Provide a brief explanation for each."
        )),
        HumanMessage(content=(
            f"Claims to verify:\n{claims}\n\n"
            f"Search results:\n{verification_results}"
        ))
    ])
    # Add the extraction logic here!
    if isinstance(verification.content, list):
        clean_verification = verification.content[0]["text"]
    else:
        clean_verification = verification.content
    return {"fact_check": clean_verification}

def writer(state: BlogState) -> dict:
    fact_check = state.get("fact_check", "")
    context = f"Research notes:\n{state['research']}"
    if fact_check:
        context += f"\n\nFact-check report:\n{fact_check}"

    response = llm.invoke([
        SystemMessage(content=(
            "You are a blog writer. Write an engaging, well-structured blog "
            "post based on the research provided. If a fact-check report is "
            "included, only use claims marked as VERIFIED. Include an "
            "introduction, clear sections with headings, and a conclusion. "
            "Aim for 500-800 words."
        )),
        HumanMessage(content=(
            f"Topic: {state['topic']}\n\n{context}"
        ))
    ])
    # Extract the clean text before saving it to the state
    if isinstance(response.content, list):
        clean_draft = response.content[0]["text"]
    else:
        clean_draft = response.content
    return {"draft": clean_draft}

def supervisor(state: BlogState) -> dict:
    research = state.get("research", "")
    fact_check = state.get("fact_check", "")
    draft = state.get("draft", "")

    response = llm.invoke([
        SystemMessage(content=(
            "You are a supervisor managing a blog writing team. "
            "Your team has three specialists:\n"
            "- researcher: searches the web and gathers information\n"
            "- fact_checker: verifies claims from the research\n"
            "- writer: writes blog posts from verified research\n\n"
            "The correct workflow order is: researcher -> fact_checker -> writer\n"
            "Based on the current state, decide who should work next.\n"
            "If research is not done, respond: researcher\n"
            "If research is done but fact-check is not, respond: fact_checker\n"
            "If both are done but draft is not, respond: writer\n"
            "If everything is done, respond: FINISH\n\n"
            "Respond with ONLY one word: researcher, fact_checker, writer, or FINISH"
        )),
        HumanMessage(content=(
            f"Topic: {state['topic']}\n"
            f"Research done: {'yes' if research else 'no'}\n"
            f"Fact-check done: {'yes' if fact_check else 'no'}\n"
            f"Draft done: {'yes' if draft else 'no'}"
        ))
    ])

    if isinstance(response.content, list):
        raw_text = response.content[0]["text"]
    else:
        raw_text = response.content

    decision = raw_text.strip().lower()
    if "researcher" in decision:
        return {"next_step": "researcher"}
    elif "fact_checker" in decision:
        return {"next_step": "fact_checker"}
    elif "writer" in decision:
        return {"next_step": "writer"}
    else:
        return {"next_step": "FINISH"}
    
def route_next(state: BlogState) -> str:
    next_step = state.get("next_step", "FINISH")
    if next_step == "researcher":
        return "researcher"
    elif next_step == "fact_checker":
        return "fact_checker"
    elif next_step == "writer":
        return "writer"
    else:
        return END
    

# Create the graph with BlogState as the shared state
graph = StateGraph(BlogState)

# Register each agent as a node
graph.add_node("supervisor", supervisor)
graph.add_node("researcher", researcher)
graph.add_node("fact_checker", fact_checker)
graph.add_node("writer", writer)

# Wire the edges: START -> supervisor, then conditional routing
graph.add_edge(START, "supervisor")
graph.add_conditional_edges("supervisor", route_next, ["researcher", "fact_checker", "writer", END])
graph.add_edge("researcher", "supervisor")
graph.add_edge("fact_checker", "supervisor")
graph.add_edge("writer", END)

# Set up checkpointer for state persistence
checkpointer = MemorySaver()
app = graph.compile(checkpointer=checkpointer, interrupt_before=["writer"])
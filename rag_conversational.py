import os
from dotenv import load_dotenv

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader
from langchain_community.embeddings import JinaEmbeddings

from langchain_community.vectorstores import TiDBVectorStore

from sqlalchemy import create_engine, inspect

from langchain_openai import AzureChatOpenAI
from langchain.schema import AIMessage, HumanMessage, SystemMessage

from langchain.chains import create_history_aware_retriever, create_retrieval_chain

from langchain.chains.combine_documents import create_stuff_documents_chain

from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder

load_dotenv()

# define the directory containing the text file
current_dir = os.path.dirname(os.path.abspath(__file__))  # to get the current directory of this py file
file_path = os.path.join(current_dir, "data", "History.txt")  # to get the path of the text file relative to the current directory

# Ensure the text file exists
if not os.path.exists(file_path):
    raise FileNotFoundError(
        f"The file {file_path} does not exist. Please check the path."
    )
    
# TiDB Serverless connection
TIDB_DATABASE_URL = os.getenv('TIDB_DATABASE_URL')
assert TIDB_DATABASE_URL is not None

engine = create_engine(url=TIDB_DATABASE_URL, pool_recycle=300) 

tidb_connection_string = os.getenv('TIDB_DATABASE_URL')

# the table name in TiDB
TABLE_NAME = "langchain_vector"

# define the JINA AI API key
JINAAI_API_KEY = os.getenv('JINAAI_API_KEY')
assert JINAAI_API_KEY is not None

# define the function to generate embeddings
embeddings = JinaEmbeddings(
    jina_api_key=JINAAI_API_KEY, model_name="jina-embeddings-v2-base-en"
)

loader = TextLoader(file_path, encoding='utf-8')
documents = loader.load()

# Split the document into chunks
text_splitter = RecursiveCharacterTextSplitter(chunk_size=200, chunk_overlap=0)
docs = text_splitter.split_documents(documents)
print(f"Doc split done, Number of documents: {len(docs)}")

# intialize the instance for TiDBVectorStore
db = TiDBVectorStore(
    embedding_function=embeddings,
    connection_string=tidb_connection_string,
    distance_strategy="cosine",  # default, another option is "l2"
    drop_existing_table=False,
)

# Check if the table exists

inspector = inspect(engine)
if not inspector.has_table(TABLE_NAME):    
    # Create the table if it does not exist
    
    print(f"Added the new docs to the table {TABLE_NAME}")
    
    db.add_documents(docs)
    print(f"Added {len(docs)} documents to the table {TABLE_NAME}")
else:
    print(f"Table {TABLE_NAME} already exists")
    
# The query to search for
query = "What are the different types of soil?"

# using the db as retriver with similarity_score_threshold
retriever = db.as_retriever(
    search_type="similarity_score_threshold",
    search_kwargs={"k": 3, "score_threshold": 0.5},
)

docs_retreived = retriever.invoke(query)

# Display the relevant results with metadata
print("\n--- Relevant Documents ---")
for i, doc in enumerate(docs_retreived, 1):
    print(f"Document {i}:\n{doc.page_content}\n")
    if doc.metadata:
        print(f"Source: {doc.metadata.get('source', 'Unknown')}\n")
        

# combine the query and the relevant documents
combined_input = (
    "Here are some documents that might help answer the question:"
    + query
    + "\n\n Relevant Documents:\n"
    + "\n\n".join([doc.page_content for doc in docs_retreived])
    + "\n\nPlease provide an answer based only on the provided documents. If the answer is not found in the documents, respond with 'I'm not sure'."
)

# Create a ChatOpenAI model
model = AzureChatOpenAI(
    temperature=0,
    azure_deployment=os.environ["AZURE_OPENAI_DEPLOYMENT_NAME"],
    openai_api_version=os.environ["AZURE_OPENAI_API_VERSION"],
    )

# Define the messages for the model
messages = [
    SystemMessage(content="You are a helpful assistant."),
    HumanMessage(content=combined_input),
]

#invoke the model with combined input
result = model.invoke(messages)

# Display the full result and content only
print("\n--- Generated Response ---")
# print("Full result:")
# print(result)
print("Content only:")
print(result.content)

# Contextualize question prompt
# This system prompt helps the AI understand that it should reformulate the question
# based on the chat history to make it a standalone question
contextualize_q_system_prompt = (
    "Given a chat history and the latest user question "
    "which might reference context in the chat history, "
    "formulate a standalone question which can be understood "
    "without the chat history. Do NOT answer the question, just "
    "reformulate it if needed and otherwise return it as is."
)

# Create a prompt template for contextualizing questions
contextualize_q_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", contextualize_q_system_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ]
)

# Create a history-aware retriever
# This uses the LLM to help reformulate the question based on chat history
history_aware_retriever = create_history_aware_retriever(
    model, retriever, contextualize_q_prompt
)

### Answer question ###
#  This system prompt helps the AI understand that it should provide concise answers
# based on the retrieved context and indicates what to do if the answer is unknown
qa_system_prompt = (
    "You are an assistant for question-answering tasks. "
    "Use the following pieces of retrieved context to answer "
    "the question. If you don't know the answer, say that you "
    "don't know. Use three sentences maximum and keep the "
    "answer concise."
    "\n\n"
    "{context}"
)

# Create a prompt template for answering questions
qa_prompt = ChatPromptTemplate.from_messages([
    ("system", qa_system_prompt),
    MessagesPlaceholder("chat_history"),
    ("human", "{input}"),
])

# `create_stuff_documents_chain` feeds all retrieved context into the LLM
question_answer_chain = create_stuff_documents_chain(model, qa_prompt)

# Create a retrieval chain that combines the history-aware retriever and the question answering chain
rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)

# function to start the continual chat
def continual_chat():
    print("Starting continual chat...")
    print("Type 'exit' to end the chat.")
    chat_history = []   # collect the chat history
    while True:
        query = input("you:") # get the user input
        if query.lower() == 'exit': # check if the user wants to exit
            break
        
        # process the user's query through retrieval chain
        result = rag_chain.invoke({"input": query, "chat_history": chat_history})
        
        print("RAG response:", result['answer'])
        
        # update the chat history
        chat_history.append(HumanMessage(content=query))
        chat_history.append(SystemMessage(content=result["answer"]))
        
# Main function to start the continual chat
if __name__ == "__main__":
    continual_chat()
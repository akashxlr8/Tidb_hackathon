import os
import reflex as rx
from dotenv import load_dotenv

import openai
load_dotenv()

# Checking if the API key is set properly
if not os.getenv("AZURE_OPENAI_API_KEY"):
    raise Exception("Please set AZURE_OPENAI_API_KEY environment variable.")

class QA(rx.Base):
    """A question and answer pair."""

    question: str
    answer: str


DEFAULT_CHATS = {
    "Intros": [],
}

class chat_state(rx.State):
    """ The chat state """
    
    # A dict from the chat name to the list of questions and answers.
    chats: dict[str, list[QA]] = DEFAULT_CHATS
    
    # The current chat name.
    current_chat = "Intros"

    # The current question.
    question: str

    # Whether we are processing the question.
    processing: bool = False

    # The name of the new chat.
    new_chat_name: str = ""

    def create_chat(self):
        """Create a new chat."""
        # Add the new chat to the list of chats.
        self.current_chat = self.new_chat_name
        self.chats[self.new_chat_name] = []

    def delete_chat(self):
        """Delete the current chat."""
        del self.chats[self.current_chat]
        if len(self.chats) == 0:
            self.chats = DEFAULT_CHATS
        self.current_chat = list(self.chats.keys())[0]

    def set_chat(self, chat_name: str):
        """Set the name of the current chat.

        Args:
            chat_name: The name of the chat.
        """
        self.current_chat = chat_name

    @rx.var
    def chat_titles(self) -> list[str]:
        """Get the list of chat titles.

        Returns:
            The list of chat names.
        """
        return list(self.chats.keys())
    
    async def process_question(self, form_data: dict[str, str]):
        # Get the question from the form
        question = form_data["question"]

        # Check if the question is empty
        if question == "":
            return
        
        # The openai process question is being called here, need to look into this
        model = self.openai_process_question

        async for value in model(question):
            yield value

    # this fucntion handles the openai processing of the question
    async def openai_process_question(self, question: str):
        """Get the response from the API.

        Args:
            form_data: A dict with the current question.
        """

        # Add the question to the list of questions.
        qa = QA(question=question, answer="")
        self.chats[self.current_chat].append(qa)

        # Clear the input and start the processing.
        self.processing = True
        yield

        # Build the messages.
        messages = [
            {
                "role": "system",
                "content": "You are a friendly chatbot named Reflex. Respond in markdown.",
            }
        ]
        
        # Add the question and answer to the messages
        for qa in self.chats[self.current_chat]:
            messages.append({"role": "user", "content": qa.question})
            messages.append({"role": "assistant", "content": qa.answer})

        # Remove the last mock answer.
        messages = messages[:-1]
        
        # Set the openai api type to azure
        openai.api_type = "azure"
        
        # Create a new instance of the AzureOpenAI class
        azure_openai_client = openai.AzureOpenAI(
            api_key = os.getenv("AZURE_OPENAI_API_KEY"), 
            # api_version = get_secret('GprntAICTDevOpenAIVersion'), 
            api_version = os.getenv("OPENAI_API_VERSION"),
            azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT"),
        )

        # Start a new session to answer the question.
        session = azure_openai_client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL"),
            messages=messages,
            stream=True,
        )
        
        
         # Stream the results, yielding after every word.
        for chunk in session:
            try:
                if chunk.choices[-1].delta.content != None:
                    # print(chunk.choices[-1].delta.content, end='')
                    if not None:
                        qa.answer += chunk.choices[-1].delta.content
                        yield
            except Exception as e:
                pass
        
        self.processing = False
        self.chats = self.chats
        
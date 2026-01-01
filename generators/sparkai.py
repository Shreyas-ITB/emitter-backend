from langchain.schema import Document
from langchain.schema.runnable import RunnablePassthrough
from langchain_community.vectorstores import Chroma
from langchain_community.chat_models import ChatOllama
from langchain_community.embeddings import FastEmbedEmbeddings
from langchain.schema.output_parser import StrOutputParser
from langchain.prompts.chat import ChatPromptTemplate
from langchain_core.globals import set_verbose, set_debug
from handlers.config import posts_collection  # Assuming this is the MongoDB collection

set_debug(False)
set_verbose(False)

class ChatSpark:
    vector_store = None
    retriever = None
    chain = None

    def __init__(self, llm_model: str = "llava:7b"):
        self.model = ChatOllama(model=llm_model)
        self.prompt = ChatPromptTemplate(
            [
                (
                    "system",
                    "You are Spark, the cute, intelligent, and friendly assistant for emitter.dev, created by emitter.dev developers. Your job is to help users with their questions, especially about posts on the platform. Be kind, understanding, and accurate in your responses.",
                ),
                (
                    "human",
                    "Here is the context: {context}\nQuestion: {question}",
                ),
            ]
        )

        self.vector_store = None
        self.retriever = None
        self.chain = None

    async def spark_answer(self, post_ids: list = None, question: str = "") -> str:
        """
        Answer questions either based on specific post content (single or multiple post IDs) or general knowledge.

        Args:
            post_ids (list, optional): A list of post IDs to fetch content from. Defaults to None.
            question (str): The question to ask.

        Returns:
            str: The AI's response to the question.
        """
        if post_ids:
            # If post_ids is a list, fetch content for all posts
            post_context = ""
            if isinstance(post_ids, list):
                for post_id in post_ids:
                    post = await posts_collection.find_one({"post_id": post_id})
                    if post:
                        post_content = f"""
                        Heading: {post.get("heading", "N/A")}
                        TL;DR: {post.get("tldr", "N/A")}
                        Description: {post.get("description", "N/A")}
                        Tags: {", ".join(post.get("tags", []))}
                        """
                        post_context += post_content + "\n\n"  # Concatenate post content
                    else:
                        post_context += f"Post with ID {post_id} not found.\n\n"
            else:
                return "post_ids should be a list."

        else:
            # If no post_ids are provided, use general knowledge context
            post_context = "I am Spark, ready to assist you with any question!"

        # Wrap the context in a Document object for Chroma compatibility
        document = Document(page_content=post_context)

        # Create a vector store using the combined post context or general knowledge
        documents = [document]  # Now Chroma expects a list of Document objects
        self.vector_store = Chroma.from_documents(
            documents=documents,
            embedding=FastEmbedEmbeddings(),
            persist_directory="chroma_db",
        )

        # Create the retriever
        self.retriever = self.vector_store.as_retriever(
            search_type="similarity_score_threshold",
            search_kwargs={"k": 10, "score_threshold": 0.0},
        )

        # Set up the chain for question-answering
        self.chain = (
            {"context": self.retriever, "question": RunnablePassthrough()}
            | self.prompt
            | self.model
            | StrOutputParser()
        )

        # Handle the case where the chain isn't set up
        if not self.chain:
            return "Something went wrong while setting up the chain."

        # Run the chain with the question
        response = self.chain.invoke({"question": question, "context": post_context})

        return response

    def clear(self):
        """Clears the vector store, retriever, and chain."""
        self.vector_store = None
        self.retriever = None
        self.chain = None

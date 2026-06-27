# User Workflow

This document outlines the end-to-end user journey when interacting with **pdf-GPT**.

## 1. Configuration & Setup
1. **Launch**: The user opens the web application in their browser (`http://localhost:1212`).
2. **Settings**: The user navigates to the sidebar settings pane.
3. **Provider Selection**: The user selects their preferred AI provider (OpenAI, Gemini, or a local Ollama model).
4. **API Key**: If using a cloud provider, the user inputs their API key. This is securely saved via the FastAPI backend to a local configuration file.

## 2. Document Ingestion
1. **Upload**: The user drags and drops one or more PDF files into the file uploader widget.
2. **Processing**: The user clicks "Process". A progress bar appears as the frontend sends the files to the `/api/upload` endpoint.
3. **Confirmation**: Once the backend finishes extracting text, creating chunks, and generating embeddings, the UI notifies the user that the document is ready for querying.

## 3. Conversational Interaction
1. **Query**: The user types a question into the chat input box at the bottom of the screen.
2. **Streaming Response**: The question is sent to the `/api/chat` endpoint. The frontend listens to the HTTP stream and types out the response in real-time, providing a fluid, ChatGPT-like experience.
3. **Follow-up**: The user can continue asking questions. The conversational history is maintained in the frontend state and sent with each request to provide conversational context to the LLM.

## 4. Reset & Cleanup
1. **Clear Chat**: The user can click "Clear Chat" to wipe the conversation history while keeping the loaded PDF in memory.
2. **Clear Memory**: The user can click "Clear Memory" to purge the backend vector store and upload new, unrelated documents.

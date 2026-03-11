# Multimodal Document Processing and Query System

This project implements a Flask-based web application that allows users to upload PDF documents, extract and summarize their content (text, images, and tables), and query the processed data using a natural language interface. The application leverages OpenAI's GPT models and FAISS for vector-based retrieval.

![Screenshot 2025-01-19 001808](https://github.com/user-attachments/assets/4ac7f361-db7f-4d17-9673-a65677e97cfe)


---

## Table of Contents
1. [Features](#features)
2. [Technologies Used](#technologies-used)
3. [Setup Instructions](#setup-instructions)
4. [Application Workflow](#application-workflow)
5. [Usage](#usage)

---

## Features
- Upload and process PDF files.
- Extract text, images, and tables from documents.
- Summarize extracted content using OpenAI's GPT models.
- Store summarized content in a vector database (FAISS).
- Perform semantic queries to retrieve and display relevant information.

---

## Technologies Used
- **Flask**: For building the web application.
- **OpenAI GPT Models**: For summarizing content and generating answers.
- **FAISS**: For efficient vector-based document retrieval.
- **Unstructured**: For PDF content extraction.
- **Pillow**: For image processing.
- **LangChain**: To orchestrate LLM workflows.

---

## Setup Instructions

### Prerequisites
- Python 3.8+
- An OpenAI API key
- Installed dependencies from `requirements.txt`

### Installation Steps
1. Clone the repository:
   ```bash
   git clone https://github.com/your-repo-url.git
   cd your-repo-url
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set up environment variables:
   Create a `.env` file with your OpenAI API key:
   ```env
   OPENAI_API_KEY=your_openai_api_key
   ```
4. Run the Flask app:
   ```bash
   python app.py
   ```
5. Access the app in your browser at [http://127.0.0.1:5000](http://127.0.0.1:5000).

---

## Application Workflow

### 1. **Upload a PDF Document**
   - The user uploads a PDF file via the application interface.
   - Allowed file types: `.pdf`

### 2. **Content Extraction**
   - The application uses `unstructured.partition.pdf` to extract content into:
     - Text blocks
     - Images
     - Tables

### 3. **Content Summarization**
   - Text and table summaries are generated using GPT-4.
   - Images are summarized using a dedicated GPT-based workflow.

### 4. **Store in Vector Database**
   - Summarized content is stored in a FAISS vector database for efficient semantic retrieval.

### 5. **Query the System**
   - The user submits a natural language query.
   - Relevant content is retrieved from FAISS and a detailed response is generated.
   - Relevant images are displayed alongside textual answers.

---

## Usage

### Uploading a Document
1. Navigate to the upload page.
2. Select a PDF file and click "Upload."
3. Wait for the processing to complete.

### Querying the System
1. Enter a natural language query in the query box.
2. Click "Submit."
3. View the detailed response and associated images (if any).

---

## Future Improvements
- Support for additional file formats (e.g., `.docx`, `.xlsx`).
- Enhanced image summarization with computer vision techniques.
- Multi-language support for queries and summarization.

---

## License
This project is licensed under the MIT License.



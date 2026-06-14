import os
import uuid
import base64
from flask import Flask, request, jsonify, render_template
from werkzeug.utils import secure_filename
from unstructured.partition.pdf import partition_pdf
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.messages import HumanMessage

app = Flask(__name__)
load_dotenv()

os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

UPLOAD_FOLDER = './uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs('./raw_elements', exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['ALLOWED_EXTENSIONS'] = {'pdf'}

db = None

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def create_document(text, text_summary, image_base64_list, image_summary, table, table_summary):
    documents = []
    for t, ts in zip(text, text_summary):
        doc = Document(page_content=ts, metadata={"id": str(uuid.uuid4()), "type": "text", "original_content": t})
        documents.append(doc)
    for img, ims in zip(image_base64_list, image_summary):
        doc = Document(page_content=ims, metadata={"id": str(uuid.uuid4()), "type": "image", "original_content": img})
        documents.append(doc)
    for tb, tbs in zip(table, table_summary):
        doc = Document(page_content=tbs, metadata={"id": str(uuid.uuid4()), "type": "text", "original_content": tb})
        documents.append(doc)
    return documents

@app.route('/')
def upload_file():
    return render_template('upload.html')

@app.route('/upload', methods=['POST'])
def handle_upload():
    global db

    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        print("File Uploaded!")
        import shutil
        shutil.rmtree('./raw_elements')
        os.makedirs('./raw_elements', exist_ok=True)
        raw_element = partition_pdf(
            filename=file_path,
            strategy="fast",
            extract_images_in_pdf=True,
            extract_image_block_types=["Image", "Table"],
            extract_image_block_to_payload=False,
            extract_image_block_output_dir="./raw_elements"
        )
        print("Elements extracted!")

        Text, Images, Table = [], [], []
        for element in raw_element:
            t = str(type(element))
            if "Text" in t or "NarrativeText" in t or "ListItem" in t or "FigureCaption" in t or "Title" in t:
                Text.append(str(element))
            elif "Table" in t:
                Table.append(str(element))
            elif "Image" in t:
                Images.append(str(element))

        model = ChatGroq(temperature=0, model="llama-3.3-70b-versatile")

        prompt_text = "Summarize this text concisely: {element}"
        text_prompt = ChatPromptTemplate.from_template(prompt_text)
        text_chain = text_prompt | model | StrOutputParser()
        if Text:
            combined_text = "\n\n".join(Text)
            text_summary = [text_chain.invoke({"element": combined_text})]
            Text = [combined_text]
        else:
            text_summary = []
        print("Text summarized!")

        prompt_table = "Summarize this table concisely: {element}"
        table_prompt = ChatPromptTemplate.from_template(prompt_table)
        table_chain = table_prompt | model | StrOutputParser()
        if Table:
            combined_table = "\n\n".join(Table)
            table_summary = [table_chain.invoke({"element": combined_table})]
            Table = [combined_table]
        else:
            table_summary = []
        print("Tables summarized!")

        image_base64_list = []
        image_summaries = []
        for img_path in os.listdir("raw_elements"):
            if img_path.endswith(".jpg"):
                with open(os.path.join("raw_elements", img_path), "rb") as f:
                    image_base64_list.append(base64.b64encode(f.read()).decode("utf-8"))
                image_summaries.append("Image extracted from document.")
        print("Images processed!")

        document = create_document(Text, text_summary, image_base64_list, image_summaries, Table, table_summary)
        db = FAISS.from_documents(documents=document, embedding=HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2"))
        print("Vectorstore created!")

        return jsonify({"message": "File uploaded and processed successfully. Ready for questions!"})

    return jsonify({"error": "Invalid file type"}), 400

@app.route('/query', methods=['POST'])
def handle_query():
    global db
    if not db:
        return jsonify({"error": "No document has been uploaded yet."}), 400

    data = request.get_json()
    query = data.get("query", "")
    if not query:
        return jsonify({"error": "Query is required"}), 400

    try:
        model = ChatGroq(temperature=0, model="llama-3.3-70b-versatile")
        prompt_text = """
        You are an AI assistant.
        Answer the question based only on the following context:
        {context}
        Question: {question}
        If unsure, say "Sorry, I don't have much information about it."
        Answer:
        """
        prompt = ChatPromptTemplate.from_template(prompt_text)
        chain = prompt | model | StrOutputParser()

        relevant_documents = db.similarity_search(query)
        context = ""
        relevant_images = []
        for doc in relevant_documents:
            if doc.metadata["type"] == "text":
                context += doc.metadata["original_content"]
            elif doc.metadata["type"] == "image":
                context += doc.page_content
                relevant_images.append(doc.metadata["original_content"])

        answer = chain.invoke({"context": context, "question": query})

        html_image = ""
        if relevant_images:
            for image_base64 in relevant_images:
                html_image = f'<img src="data:image/jpeg;base64,{image_base64}" alt="Image" style="width:300px;"/>'

        return jsonify({"answer": answer, "html_image": html_image})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)

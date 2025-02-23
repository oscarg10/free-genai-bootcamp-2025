import chromadb
from chromadb.utils import embedding_functions
import json
import os
import boto3
from typing import Dict, List, Optional

class BedrockEmbeddingFunction(embedding_functions.EmbeddingFunction):
    def __init__(self, model_id="amazon.titan-embed-text-v1"):
        """Initialize Bedrock embedding function"""
        self.bedrock_client = boto3.client('bedrock-runtime', region_name="us-east-1")
        self.model_id = model_id

    def __call__(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts using Bedrock"""
        embeddings = []
        for text in texts:
            try:
                response = self.bedrock_client.invoke_model(
                    modelId=self.model_id,
                    body=json.dumps({
                        "inputText": text
                    })
                )
                response_body = json.loads(response['body'].read())
                embedding = response_body['embedding']
                embeddings.append(embedding)
            except Exception as e:
                print(f"Error generating embedding: {str(e)}")
                # Return a zero vector as fallback
                embeddings.append([0.0] * 1536)  # Titan model uses 1536 dimensions
        return embeddings

class QuestionVectorStore:
    def __init__(self, persist_directory: str = None):
        """Initialize the vector store for German A1 listening questions"""
        if persist_directory is None:
            # Get the absolute path of the current file's directory
            current_dir = os.path.dirname(os.path.abspath(__file__))
            # Use the existing vectorstore folder in data
            persist_directory = os.path.join(current_dir, "data", "vectorstore")
            
        self.persist_directory = persist_directory
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(path=persist_directory)
        
        # Use Bedrock's Titan embedding model
        self.embedding_fn = BedrockEmbeddingFunction()
        
        # Create or get collections for each section type
        self.collections = {
            "section1": self.client.get_or_create_collection(
                name="section1_questions",
                embedding_function=self.embedding_fn,
                metadata={"description": "German A1 listening comprenhension questions First Dialog - Section 1"}
            ),
            "section2": self.client.get_or_create_collection(
                name="section2_questions",
                embedding_function=self.embedding_fn,
                metadata={"description": "German A1 listening comprehension questions Second Dialog - Section 2"}
            )
        }

    def add_questions(self, section_num: int, questions: List[Dict], video_id: str):
        """Add questions to the vector store"""
        if section_num not in [1, 2]:
            raise ValueError("Only sections 1 and 2 are currently supported")
            
        collection = self.collections[f"section{section_num}"]
        
        ids = []
        documents = []
        metadatas = []
        
        for idx, question in enumerate(questions):
            # Create a unique ID for each question
            question_id = f"{video_id}_{section_num}_{idx}"
            ids.append(question_id)
            
            # Store the full question structure as metadata
            metadatas.append({
                "video_id": video_id,
                "section": section_num,
                "question_index": idx,
                "full_structure": json.dumps(question)
            })
            
            # Create a searchable document from the question content
            if section_num == 1:
                document = f"""
                Context: {question.get('Context', '')}
                Conversation: {question.get('Conversation', '')}
                Question: {question.get('Question', '')}
                """
            else:  # section 2
                document = f"""
                Context: {question.get('Context', '')}
                Question: {question.get('Question', '')}
                """
            documents.append(document)
        
        # Add to collection
        collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )

    def search_similar_questions(
        self, 
        section_num: int, 
        query: str, 
        n_results: int = 5
    ) -> List[Dict]:
        """Search for similar questions in the vector store"""
        if section_num not in [1, 2]:
            raise ValueError("Only sections 1 and 2 are currently supported")
            
        collection = self.collections[f"section{section_num}"]
        
        results = collection.query(
            query_texts=[query],
            n_results=n_results,
            include=["metadatas", "distances"]
        )
        
        # Convert results to more usable format
        questions = []
        if results['metadatas'] and results['metadatas'][0]:
            for idx, metadata in enumerate(results['metadatas'][0]):
                question_data = json.loads(metadata['full_structure'])
                question_data['similarity_score'] = results['distances'][0][idx]
                questions.append(question_data)
            
        return questions

    def get_question_by_id(self, section_num: int, question_id: str) -> Optional[Dict]:
        """Retrieve a specific question by its ID"""
        if section_num not in [1, 2]:
            raise ValueError("Only sections 1 and 2 are currently supported")
            
        collection = self.collections[f"section{section_num}"]
        
        result = collection.get(
            ids=[question_id],
            include=['metadatas']
        )
        
        if result['metadatas']:
            return json.loads(result['metadatas'][0]['full_structure'])
        return None

    def parse_questions_from_file(self, filename: str) -> List[Dict]:
        """Parse questions from a structured text file"""
        questions = []
        current_question = {}
        
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            i = 0
            while i < len(lines):
                line = lines[i].strip()
                
                if line.startswith('<question>'):
                    current_question = {}
                elif line.startswith('Context:'):
                    i += 1
                    if i < len(lines):
                        current_question['Context'] = lines[i].strip()
                elif line.startswith('Conversation:'):
                    i += 1
                    if i < len(lines):
                        current_question['Conversation'] = lines[i].strip()
                elif line.startswith('Question:'):
                    i += 1
                    if i < len(lines):
                        current_question['Question'] = lines[i].strip()
                elif line.startswith('Options:'):
                    options = []
                    i += 1
                    while i < len(lines) and lines[i].strip().startswith(('A)', 'B)', 'C)', 'D)')):
                        options.append(lines[i].strip())
                        i += 1
                    current_question['Options'] = options
                    i -= 1  # Back up one since we'll increment at end of loop
                elif line.startswith('</question>'):
                    if current_question:  # Only add if we have question data
                        questions.append(current_question.copy())
                        current_question = {}
                i += 1
                
            return questions
        except Exception as e:
            print(f"Error parsing questions from {filename}: {str(e)}")
            return []

    def index_questions_file(self, filename: str, section_num: int):
        """Index all questions from a file into the vector store"""
        # Extract video ID from filename
        video_id = os.path.basename(filename).split('_section')[0]
        
        # Parse questions from file
        questions = self.parse_questions_from_file(filename)
        
        # Add to vector store
        if questions:
            self.add_questions(section_num, questions, video_id)
            print(f"Indexed {len(questions)} questions from {filename}")

def print_results(results):
    for result in results:
        print(f"\nSimilarity score: {result.get('similarity_score', '')}")
        print(f"Context: {result.get('Context', '')}")
        print(f"Conversation: {result.get('Conversation', '')}")
        print(f"Question: {result.get('Question', '')}")
        print("Options:")
        for option in result.get('Options', []):
            print(f"  {option}")
        print()

if __name__ == "__main__":
    # Example usage
    store = QuestionVectorStore()
    
    # Get the absolute path to the questions directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    questions_dir = os.path.join(current_dir, "data", "questions")
    
    # Index questions from files
    question_files = [
        (os.path.join(questions_dir, "tlYgH1pK4rQ_dialog1_lutz.txt"), 1),
        (os.path.join(questions_dir, "tlYgH1pK4rQ_dialog2_johannes.txt"), 2)
    ]
    
    for filename, section_num in question_files:
        if os.path.exists(filename):
            store.index_questions_file(filename, section_num)
        else:
            print(f"Warning: File not found: {filename}")
    
    # Search for similar questions
    print("\nSearching Dialog 1 (Lutz):")
    similar = store.search_similar_questions(1, "Fragen über Sprachen und Wohnort", n_results=2)
    print_results(similar)
    
    print("\nSearching Dialog 2 (Johannes):")
    similar = store.search_similar_questions(2, "Fragen über Beruf und Familie", n_results=2)
    print_results(similar)
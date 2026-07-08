import asyncio
import json
import os
import uuid
import zipfile
import tempfile
import sys
from pathlib import Path
from datetime import datetime

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlmodel import select, SQLModel
from app.models.models import Assignment, Student, Submission, SubmissionSourceType, SubmissionStatus

from app.core.config import settings

# Connect to DB
engine = create_async_engine(settings.DATABASE_URL)
async_session = async_sessionmaker(engine, expire_on_commit=False)

from app.services.storage_service import StorageService

async def main():
    async with async_session() as session:
        # Get Week 12 assignment
        stmt = select(Assignment).where(Assignment.slug == "week12")
        result = await session.execute(stmt)
        assignment = result.scalar_one_or_none()
        if not assignment:
            print("Week 12 assignment not found!")
            return

        # Get first student
        stmt = select(Student).limit(1)
        result = await session.execute(stmt)
        student = result.scalar_one_or_none()
        if not student:
            print("No student found!")
            return

        # 1. Create a valid submission in a temp directory
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # requirements.txt
            with open(temp_path / "requirements.txt", "w") as f:
                f.write("scikit-learn\n")
            
            # README.md
            with open(temp_path / "README.md", "w") as f:
                f.write("# Semantic Search Engine\n\nThis is a fully functioning semantic search engine using TF-IDF and cosine similarity.\nIt supports building an index from JSON documents and querying them interactively.\n")
            
            # build_index.py
            with open(temp_path / "build_index.py", "w") as f:
                f.write("""import json
import os
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer

def build():
    documents = []
    filenames = []
    
    if os.path.isdir('corpus'):
        for f in os.listdir('corpus'):
            if f.endswith('.json'):
                path = os.path.join('corpus', f)
                with open(path, 'r') as fh:
                    doc = json.load(fh)
                    documents.append(doc.get('content', ''))
                    filenames.append(f)
                    
    if not documents:
        documents = ["dummy"]
        filenames = ["dummy"]
        
    vectorizer = TfidfVectorizer(stop_words='english')
    tfidf_matrix = vectorizer.fit_transform(documents)
    
    with open('index.pkl', 'wb') as f:
        pickle.dump({'vectorizer': vectorizer, 'matrix': tfidf_matrix, 'filenames': filenames}, f)
        
if __name__ == '__main__':
    build()
""")

            # query.py
            with open(temp_path / "query.py", "w") as f:
                f.write("""import pickle
from sklearn.metrics.pairwise import cosine_similarity
import sys

def main():
    try:
        with open('index.pkl', 'rb') as f:
            data = pickle.load(f)
    except FileNotFoundError:
        print("index.pkl not found")
        sys.exit(1)
        
    vectorizer = data['vectorizer']
    matrix = data['matrix']
    filenames = data['filenames']
    
    while True:
        try:
            q = input("Query: ")
            if q.strip().lower() == "quit":
                break
            
            q_vec = vectorizer.transform([q])
            sim = cosine_similarity(q_vec, matrix)[0]
            
            results = [(sim[i], filenames[i]) for i in range(len(filenames)) if sim[i] > 0]
            results.sort(reverse=True)
            
            if not results:
                print("0 documents found.")
            else:
                for score, fname in results[:5]:
                    print(f"{fname} (Score: {score:.4f})")
        except EOFError:
            break

if __name__ == '__main__':
    main()
""")

            # 2. Zip it up
            zip_path = temp_path / "submission.zip"
            with zipfile.ZipFile(zip_path, 'w') as zipf:
                for root, dirs, files in os.walk(temp_path):
                    for file in files:
                        if file != "submission.zip":
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, temp_path)
                            zipf.write(file_path, arcname)
                            
            # 3. Upload to MinIO
            storage = StorageService()
            zip_key = f"student_{student.id}/week12_real_submission.zip"
            
            # Since StorageService might expect bucket_submissions to exist, we can use it
            import boto3
            s3 = boto3.client(
                's3',
                endpoint_url=settings.MINIO_ENDPOINT,
                aws_access_key_id=settings.MINIO_ACCESS_KEY,
                aws_secret_access_key=settings.MINIO_SECRET_KEY
            )
            try:
                s3.create_bucket(Bucket='submissions')
            except Exception:
                pass
            
            s3.upload_file(str(zip_path), 'submissions', zip_key)

            # 4. Create Submission Record
            submission = Submission(
                student_id=student.id,
                assignment_id=assignment.id,
                status=SubmissionStatus.COMPLETED,
                source_type=SubmissionSourceType.ZIP,
                zip_object_key=zip_key,
                submitted_at=datetime.utcnow()
            )
            session.add(submission)
            await session.commit()
            print(f"Created real Week 12 submission! ID: {submission.id}")

if __name__ == "__main__":
    asyncio.run(main())

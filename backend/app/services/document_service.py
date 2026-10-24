"""
Document Ingestion & Lifecycle Management Service
Coordinates parsing, classification, chunking, embedding generation, vector indexing, and cleanup.
"""

from typing import Any, Dict, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from backend.app.models.document import Document
from backend.app.models.chunk import DocumentChunk
from backend.app.storage.service import storage_service
from backend.app.embeddings.provider import embedding_provider
from backend.app.retrieval.vector_store import vector_store
from ingestion.parser import document_parser
from ingestion.chunker import chunker
from ml.document_classifier.predict import document_classifier


class DocumentService:
    async def process_and_index_document(
        self,
        db: AsyncSession,
        tenant_id: str,
        kb_id: str,
        filename: str,
        file_bytes: bytes,
        mime_type: str,
        user_id: str,
    ) -> Document:
        """
        Process, classify, chunk, embed, and index a document.
        """
        # 1. Multi-tenant storage
        storage_filename = f"{kb_id}_{filename}"
        storage_path = await storage_service.save_file(tenant_id, storage_filename, file_bytes)

        # 2. Document Classification
        classification_result = document_classifier.predict(filename + " " + file_bytes[:1000].decode("utf-8", errors="ignore"))
        doc_class = classification_result.get("category", "OTHER")

        # 3. Create Document DB Record
        doc = Document(
            tenant_id=tenant_id,
            kb_id=kb_id,
            filename=filename,
            storage_path=storage_path,
            file_size=len(file_bytes),
            mime_type=mime_type,
            classification=doc_class,
            status="PROCESSING",
            uploaded_by=user_id,
        )
        db.add(doc)
        await db.flush()

        try:
            # 4. Parse pages & metadata
            pages, parse_meta = document_parser.parse(filename, file_bytes)

            # 5. Structure-aware chunking
            chunks = chunker.chunk_pages(pages)

            if not chunks:
                # Fallback single chunk
                from ingestion.chunker import Chunk
                chunks = [Chunk(0, "Empty document content", 1, "General", 3)]

            # 6. Generate Batch Embeddings
            chunk_texts = [c.content for c in chunks]
            vectors = embedding_provider.embed_batch(chunk_texts)

            # 7. Create Chunk Records in DB & Vector Store payload
            db_chunks = []
            vector_payload_chunks = []
            total_tokens = 0

            for c in chunks:
                total_tokens += c.token_count
                db_chunk = DocumentChunk(
                    tenant_id=tenant_id,
                    kb_id=kb_id,
                    doc_id=doc.id,
                    chunk_index=c.chunk_index,
                    content=c.content,
                    token_count=c.token_count,
                    page_number=c.page_number,
                    section=c.section,
                    chunk_metadata=c.chunk_metadata,
                )
                db.add(db_chunk)
                await db.flush()

                vector_payload_chunks.append({
                    "chunk_id": db_chunk.id,
                    "chunk_index": c.chunk_index,
                    "content": c.content,
                    "page_number": c.page_number,
                    "section": c.section,
                    "token_count": c.token_count,
                    "filename": filename,
                })

            # 8. Index into Qdrant
            vector_store.index_chunks(
                tenant_id=tenant_id,
                kb_id=kb_id,
                doc_id=doc.id,
                chunks=vector_payload_chunks,
                vectors=vectors,
            )

            # 9. Mark Document INDEXED
            doc.status = "INDEXED"
            doc.chunk_count = len(chunks)
            doc.token_count = total_tokens
            doc.doc_metadata = parse_meta
            await db.commit()
            await db.refresh(doc)
            return doc

        except Exception as e:
            doc.status = "FAILED"
            doc.error_message = str(e)
            await db.commit()
            raise e

    async def delete_document(self, db: AsyncSession, tenant_id: str, doc_id: str) -> bool:
        """
        Delete document across DB, storage, and Qdrant vectors.
        Prevents orphaned vectors and unauthorized cross-tenant deletion.
        """
        stmt = select(Document).where(Document.id == doc_id, Document.tenant_id == tenant_id)
        result = await db.execute(stmt)
        doc = result.scalar_one_or_none()
        if not doc:
            return False

        # 1. Delete vectors in Qdrant
        vector_store.delete_by_document(tenant_id=tenant_id, doc_id=doc_id)

        # 2. Delete storage file
        try:
            await storage_service.delete_file(tenant_id=tenant_id, storage_path=doc.storage_path)
        except Exception:
            pass

        # 3. Delete DB record (cascades to chunks)
        await db.delete(doc)
        await db.commit()
        return True


document_service = DocumentService()

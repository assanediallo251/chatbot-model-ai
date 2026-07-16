import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError, bad_request
from app.db.repositories import DocumentRepository
from app.db.session import get_session
from app.schemas.document import DocumentOut, DocumentUploadResponse, UploadedDocument
from app.workers.ingestion import DocumentIngestionService, ingest_document_in_background

router = APIRouter()


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_documents(
    background_tasks: BackgroundTasks,
    files: list[UploadFile] = File(...),
    session: AsyncSession = Depends(get_session),
) -> DocumentUploadResponse:
    if not files:
        raise bad_request("Aucun fichier n'a ete fourni.")

    service = DocumentIngestionService(session)
    uploaded: list[UploadedDocument] = []
    uploaded_count = 0
    duplicate_count = 0

    try:
        for file in files:
            result, content = await service.register_upload(file)
            uploaded.append(
                UploadedDocument(
                    document=DocumentOut.model_validate(result.document),
                    duplicated=result.duplicated,
                )
            )
            if result.duplicated:
                duplicate_count += 1
            else:
                uploaded_count += 1
                if content is not None:
                    background_tasks.add_task(
                        ingest_document_in_background,
                        result.document.id,
                        content,
                    )
    except AppError as exc:
        raise bad_request(str(exc)) from exc

    return DocumentUploadResponse(
        documents=uploaded,
        uploaded_count=uploaded_count,
        duplicate_count=duplicate_count,
    )


@router.get("", response_model=list[DocumentOut])
async def list_documents(
    session: AsyncSession = Depends(get_session),
) -> list[DocumentOut]:
    documents = await DocumentRepository(session).list()
    return [DocumentOut.model_validate(document) for document in documents]


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> None:
    deleted = await DocumentRepository(session).delete(document_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document introuvable.")

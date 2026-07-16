import asyncio
from pathlib import Path

from starlette.datastructures import Headers, UploadFile

from app.db.session import AsyncSessionLocal
from app.workers.ingestion import DocumentIngestionService


async def main() -> None:
    pdf_path = Path("data/demo.pdf")
    if not pdf_path.exists():
        raise SystemExit("Place un fichier PDF dans data/demo.pdf avant d'executer ce script.")

    async with AsyncSessionLocal() as session:
        with pdf_path.open("rb") as file_obj:
            upload = UploadFile(
                filename=pdf_path.name,
                file=file_obj,
                headers=Headers({"content-type": "application/pdf"}),
            )
            result = await DocumentIngestionService(session).ingest_upload(upload)
            print(f"Indexed: {result.document.filename} ({result.document.chunk_count} chunks)")


if __name__ == "__main__":
    asyncio.run(main())

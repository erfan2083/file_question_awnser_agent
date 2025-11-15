from celery import shared_task
from documents.models import Document
from documents.services import DocumentProcessor

@shared_task
def process_document_task(document_id: int):
    """
    Celery task to process a document in the background.
    """
    try:
        document = Document.objects.get(id=document_id)
        
        # Check if already processed or failed
        if document.status not in [Document.Status.UPLOADED, Document.Status.FAILED]:
            return f"Document {document_id} is not in a state to be processed."

        processor = DocumentProcessor()
        success = processor.process_document(document)
        
        if success:
            return f"Successfully processed document {document_id}"
        else:
            return f"Failed to process document {document_id}. Check error message on document."
            
    except Document.DoesNotExist:
        return f"Document with id {document_id} does not exist."
    except Exception as e:
        # Log the error
        try:
            # Try to mark the document as failed if it exists
            doc = Document.objects.get(id=document_id)
            doc.status = Document.Status.FAILED
            doc.error_message = f"Celery task failed: {str(e)}"
            doc.save()
        except Document.DoesNotExist:
            pass # Document was not found, nothing to mark
        return f"Error processing document {document_id}: {str(e)}"
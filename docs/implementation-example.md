# Implementation Example: File Processing with Analytics

This example shows how the analytics service integrates with our file processing pipeline.

## 1. File Upload with Analytics

```python
# apps/api/routers/files.py
from fastapi import APIRouter, UploadFile, Depends
from services.analytics import log_event, EventType
from services.storage import get_storage_service

router = APIRouter()

@router.post("/api/v1/files/ingest")
async def initiate_upload(
    filename: str,
    content_type: str,
    current_user: User = Depends(get_current_user),
    storage = Depends(get_storage_service)
):
    file_id = str(uuid4())
    
    # Log analytics event
    log_event(
        EventType.FILE_UPLOAD_INITIATED.value,
        user_id=current_user.id,
        tenant_id=current_user.tenant_id,
        metadata={
            "file_id": file_id,
            "filename": filename,
            "content_type": content_type,
            "size_bytes": request.headers.get("content-length")
        }
    )
    
    # Generate presigned URL
    presigned_url = await storage.generate_upload_url(
        bucket="uploads",
        key=f"{current_user.tenant_id}/{file_id}/{filename}"
    )
    
    # Create database record
    await create_file_record(
        file_id=file_id,
        user_id=current_user.id,
        tenant_id=current_user.tenant_id,
        filename=filename,
        content_type=content_type,
        status="pending"
    )
    
    return {
        "file_id": file_id,
        "upload_url": presigned_url,
        "expires_in": 3600
    }
```

## 2. File Processing with Analytics

```python
# services/processors/file_processor.py
from celery import Celery
from services.analytics import log_event, EventType
from agents.content_mind import ContentMindAgent

celery = Celery(__name__)

@celery.task(bind=True, max_retries=3)
def process_file_task(self, file_id: str, user_id: str, tenant_id: str):
    try:
        # Log processing start
        log_event(
            EventType.AGENT_STARTED.value,
            user_id=user_id,
            tenant_id=tenant_id,
            correlation_id=self.request.id,
            metadata={
                "file_id": file_id,
                "agent": "FileProcessor",
                "attempt": self.request.retries + 1
            }
        )
        
        # Get file from storage
        file_data = storage.download_file(file_id)
        
        # Extract content based on type
        content = extract_content(file_data)
        
        # Process with ContentMind
        agent = ContentMindAgent()
        result = await agent.process({
            "content": content,
            "user_id": user_id,
            "tenant_id": tenant_id
        })
        
        # Store in knowledge repository
        knowledge_id = await store_knowledge(result)
        
        # Update file status
        await update_file_status(file_id, "completed", knowledge_id=knowledge_id)
        
        # Log success
        log_event(
            EventType.FILE_PROCESSED.value,
            user_id=user_id,
            tenant_id=tenant_id,
            correlation_id=self.request.id,
            metadata={
                "file_id": file_id,
                "knowledge_id": knowledge_id,
                "processing_time_ms": (end_time - start_time).total_seconds() * 1000,
                "tokens_used": result.get("token_count", 0)
            }
        )
        
        return {"status": "success", "knowledge_id": knowledge_id}
        
    except Exception as e:
        # Log failure
        log_event(
            EventType.FILE_FAILED.value,
            user_id=user_id,
            tenant_id=tenant_id,
            correlation_id=self.request.id,
            metadata={
                "file_id": file_id,
                "error": str(e),
                "attempt": self.request.retries + 1
            }
        )
        
        # Retry or fail
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=60 * (self.request.retries + 1))
        else:
            await update_file_status(file_id, "failed", error=str(e))
            raise
```

## 3. Digest Generation with Analytics

```python
# agents/digest_agent.py
from services.analytics import log_event, EventType

class DigestAgent(BaseAgent):
    async def generate_digest(self, user_id: str, tenant_id: str):
        try:
            # Log start
            log_event(
                EventType.DIGEST_GENERATED.value,
                user_id=user_id,
                tenant_id=tenant_id,
                metadata={
                    "type": "daily",
                    "triggered_by": "scheduled"
                }
            )
            
            # Generate digest
            items = await self.get_recent_items(user_id)
            digest = await self.create_summary(items)
            
            # Save digest
            digest_id = await self.save_digest(digest)
            
            # Send via email
            await email_gateway.send_digest(user_id, digest)
            
            # Log completion
            log_event(
                EventType.DIGEST_SENT.value,
                user_id=user_id,
                tenant_id=tenant_id,
                metadata={
                    "digest_id": digest_id,
                    "item_count": len(items),
                    "channel": "email"
                }
            )
            
            return digest_id
            
        except Exception as e:
            log_event(
                EventType.DIGEST_FAILED.value,
                user_id=user_id,
                tenant_id=tenant_id,
                metadata={
                    "error": str(e)
                }
            )
            raise
```

## 4. API Tracking with Decorator

```python
# apps/api/routers/knowledge.py
from services.analytics import track_api_call

@router.get("/api/v1/knowledge/search")
@track_api_call(EventType.API_CALLED.value)
async def search_knowledge(
    query: str,
    current_user: User = Depends(get_current_user)
):
    # This automatically logs:
    # - API endpoint called
    # - User ID
    # - Duration
    # - Success/error status
    
    results = await knowledge_repo.search(query, user_id=current_user.id)
    return {"results": results}
```

## 5. Viewing Analytics in the UI

The React frontend can display analytics data:

```typescript
// src/features/analytics/UserAnalytics.tsx
import { useEffect, useState } from 'react';
import { analyticsAPI } from '../../api/analytics';

export const UserAnalytics: React.FC = () => {
    const [summary, setSummary] = useState(null);
    
    useEffect(() => {
        const fetchAnalytics = async () => {
            const data = await analyticsAPI.getSummary(7); // Last 7 days
            setSummary(data);
        };
        
        fetchAnalytics();
    }, []);
    
    return (
        <RetroCard title="Your Activity">
            <div className="space-y-2">
                <div>Files Processed: {summary?.files_processed}</div>
                <div>Digests Created: {summary?.digests_generated}</div>
                <div>Tokens Used: {summary?.total_tokens}</div>
                <div>Storage: {summary?.storage_used_mb} MB</div>
            </div>
        </RetroCard>
    );
};
```

## Benefits

1. **Complete Traceability**: Every action is logged with user context
2. **Performance Monitoring**: Track processing times and token usage
3. **Error Tracking**: Identify failure patterns
4. **User Analytics**: Understand usage patterns
5. **Cost Attribution**: Track resource usage per tenant
6. **Debugging**: Correlation IDs link related events
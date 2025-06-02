# Task 003: Optimize ROI Workflow API Performance

## Priority: MEDIUM
## From: ARCH
## Prerequisites: Task 002 (E2E Tests) ✅ ALMOST COMPLETED by CC

## 🎯 Objective

Optimize the ROI Workflow API performance to ensure fast, responsive user experience and prepare for production scalability.

## 📋 Current Performance Analysis

Based on the ROI workflow implementation, identify optimization opportunities in:

### 1. API Response Times
Current benchmarks to improve:
- File upload processing: Currently ~2-5 seconds
- Transcription API calls: Variable based on audio length
- Translation processing: ~1-2 seconds
- Data extraction: ~1-3 seconds

**Target**: Reduce total processing time by 30% through optimization

### 2. Key Areas for Optimization

#### A. Audio Processing Pipeline
```python
# Current flow in services/roi_workflow_service.py
Upload → Transcription → Translation → Extraction → Results

# Optimization opportunities:
- Implement parallel processing where possible
- Add progress streaming to keep UI responsive
- Optimize file handling and memory usage
- Add intelligent caching for repeated processing
```

#### B. Database Operations
```python
# Optimize database interactions:
- Add proper indexing for workflow queries
- Implement connection pooling optimization
- Reduce N+1 query problems
- Add database query caching
```

#### C. API Response Structure
```python
# Optimize API responses:
- Implement streaming responses for long operations
- Add WebSocket updates for real-time progress
- Optimize JSON serialization
- Reduce payload sizes
```

## 📊 Specific Performance Tasks

### 1. Audio Processing Optimization
- **Task**: Implement parallel processing for transcription + translation
- **Current**: Sequential processing (transcribe → translate)
- **Target**: Parallel processing where audio language is detected
- **Expected Gain**: 20-30% time reduction

### 2. Caching Implementation
- **Task**: Add Redis caching for:
  - Transcription results (by audio file hash)
  - Translation results (by text + language pair)
  - Extracted data patterns
- **Expected Gain**: 50-80% reduction for repeated content

### 3. Database Query Optimization
- **Task**: Optimize database operations in `services/roi_workflow_service.py`
- **Focus Areas**:
  - Add indexes for workflow status queries
  - Optimize the workflow update patterns
  - Reduce database round trips
- **Expected Gain**: 15-25% faster database operations

### 4. Memory Management
- **Task**: Optimize memory usage for large audio files
- **Focus Areas**:
  - Streaming audio processing
  - Efficient temporary file handling
  - Memory cleanup after processing
- **Expected Gain**: Support for larger files + reduced memory footprint

### 5. API Response Streaming
- **Task**: Implement streaming responses for long operations
- **Implementation**:
  - WebSocket progress updates
  - Server-sent events for status
  - Chunked response handling
- **Expected Gain**: Better perceived performance + real-time feedback

## 🛠️ Technical Implementation Details

### Redis Caching Strategy
```python
# Implement in services/roi_workflow_service.py
class CacheService:
    async def get_transcription_cache(self, file_hash: str) -> Optional[str]
    async def set_transcription_cache(self, file_hash: str, transcript: str)
    async def get_translation_cache(self, text_hash: str, target_lang: str) -> Optional[str]
    async def set_translation_cache(self, text_hash: str, target_lang: str, translation: str)
```

### Progress Streaming
```python
# Add to main.py and roi workflow endpoints
@app.websocket("/ws/roi-workflow/{workflow_id}")
async def workflow_progress(websocket: WebSocket, workflow_id: str):
    # Stream progress updates to frontend
    pass
```

### Database Optimization
```sql
-- Add indexes for common queries
CREATE INDEX idx_workflow_status ON roi_workflows(status);
CREATE INDEX idx_workflow_created_at ON roi_workflows(created_at);
CREATE INDEX idx_workflow_user_id ON roi_workflows(user_id);
```

## 📁 Files to Modify

### Primary Files:
1. `services/roi_workflow_service.py` - Main optimization target
2. `apps/api/main.py` - Add WebSocket endpoints
3. `apps/api/routes/workflows.py` - Optimize API endpoints
4. Database migration files - Add indexes

### New Files to Create:
1. `services/cache_service.py` - Redis caching implementation
2. `services/performance_monitor.py` - Performance tracking
3. `tests/performance/` - Performance test suite

## 📈 Performance Monitoring

Implement monitoring for:
- API response times (p50, p95, p99)
- Database query performance
- Memory usage patterns
- Cache hit rates
- WebSocket connection health

## ✅ Definition of Done

1. **Performance Improvements**:
   - [ ] 30% reduction in total processing time
   - [ ] API responses under 200ms (non-processing endpoints)
   - [ ] Memory usage optimized for large files
   - [ ] Cache hit rate >70% for repeated content

2. **Technical Implementation**:
   - [ ] Redis caching implemented and working
   - [ ] WebSocket progress streaming functional
   - [ ] Database indexes added and performance improved
   - [ ] Memory leaks eliminated

3. **Testing & Validation**:
   - [ ] Performance tests created and passing
   - [ ] Load testing with concurrent requests
   - [ ] Memory usage validated under stress
   - [ ] All existing functionality preserved

4. **Documentation**:
   - [ ] Performance optimization guide documented
   - [ ] Caching strategy documented
   - [ ] Monitoring setup instructions

## 🎯 Success Metrics

- **Processing Time**: Reduced from current average to <30 seconds for typical audio
- **API Response**: <200ms for status endpoints
- **Cache Hit Rate**: >70% for transcription/translation
- **Memory Usage**: <50% reduction for large file processing
- **Concurrent Users**: Support 10+ simultaneous workflows

## 📤 Deliverables

Update your outbox.json with:
- Performance benchmarks (before/after)
- List of optimizations implemented
- Cache hit rate statistics
- Any architectural improvements made
- Recommendations for future scaling

## ⏰ Timeline

Expected completion: 4-6 hours

## 💡 Optimization Tips

1. **Start with profiling** - Identify actual bottlenecks before optimizing
2. **Measure everything** - Add timing logs to understand current performance
3. **Cache intelligently** - Focus on expensive operations (LLM calls)
4. **Stream progress** - Keep users informed during long operations
5. **Test under load** - Validate improvements with realistic usage patterns

## 🔄 Integration Notes

- Work closely with CC's E2E tests to ensure optimizations don't break functionality
- Use CA's polished UI to test real-world performance improvements
- Coordinate with frontend team for WebSocket integration

**Note**: This task focuses on backend performance. Frontend optimization may be a future task.

Begin after CC completes Task 002 and update your outbox when complete.
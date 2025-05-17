// Browser console test for file upload
// Run this in the browser console

async function testFileUpload() {
  console.log('🧪 Starting File Upload Test');
  
  // Create a test file
  const testContent = 'This is a test PDF content';
  const blob = new Blob([testContent], { type: 'application/pdf' });
  const testFile = new File([blob], 'test-upload.pdf', { type: 'application/pdf' });
  
  console.log('📄 Created test file:', testFile.name, testFile.size, 'bytes');
  
  try {
    // Import the API client
    const { filesAPI } = await import('../api/files');
    
    // Test the upload
    console.log('📤 Uploading file...');
    const result = await filesAPI.uploadFile(testFile);
    
    console.log('✅ Upload successful!');
    console.log('File ID:', result.id);
    console.log('Status:', result.status);
    
    // Check file status
    console.log('🔍 Checking file status...');
    const status = await filesAPI.getFileStatus(result.id);
    console.log('File status:', status);
    
    return result;
  } catch (error) {
    console.error('❌ Upload failed:', error);
    throw error;
  }
}

// Run the test
console.log('To test file upload, run: testFileUpload()');
window.testFileUpload = testFileUpload;
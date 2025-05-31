import React, { useState } from 'react';
import { ROIReportData } from '../../types/roi-workflow';

interface ExportOptionsProps {
  data: ROIReportData[];
  workflowId?: string;
  className?: string;
}

export function ExportOptions({ data, workflowId, className = '' }: ExportOptionsProps) {
  const [isExporting, setIsExporting] = useState(false);
  const [exportStatus, setExportStatus] = useState<string>('');

  const generateCSV = (includeHeaders = true): string => {
    const headers = [
      'Name',
      'Company', 
      'Position',
      'Discussion',
      'Contact Type',
      'Priority Level',
      'Action Items'
    ];

    const rows = data.map(item => [
      item.name,
      item.company,
      item.position,
      item.discussion,
      item.contactType,
      item.priorityLevel,
      item.actionItems.join('; ')
    ]);

    const csvContent = [
      ...(includeHeaders ? [headers] : []),
      ...rows
    ].map(row => 
      row.map(cell => 
        typeof cell === 'string' && (cell.includes(',') || cell.includes('"') || cell.includes('\n'))
          ? `"${cell.replace(/"/g, '""')}"`
          : cell
      ).join(',')
    ).join('\n');

    return csvContent;
  };

  const generateJSON = (): string => {
    return JSON.stringify(data, null, 2);
  };

  const downloadFile = (content: string, filename: string, mimeType: string) => {
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const handleExportCSV = async () => {
    setIsExporting(true);
    setExportStatus('Generating CSV...');

    try {
      const csvContent = generateCSV(true);
      const timestamp = new Date().toISOString().slice(0, 19).replace(/:/g, '-');
      const filename = `roi-report-${timestamp}.csv`;
      
      downloadFile(csvContent, filename, 'text/csv');
      setExportStatus('CSV downloaded successfully!');
      
      setTimeout(() => setExportStatus(''), 3000);
    } catch (error) {
      setExportStatus('Failed to export CSV');
      setTimeout(() => setExportStatus(''), 3000);
    } finally {
      setIsExporting(false);
    }
  };

  const handleExportJSON = async () => {
    setIsExporting(true);
    setExportStatus('Generating JSON...');

    try {
      const jsonContent = generateJSON();
      const timestamp = new Date().toISOString().slice(0, 19).replace(/:/g, '-');
      const filename = `roi-report-${timestamp}.json`;
      
      downloadFile(jsonContent, filename, 'application/json');
      setExportStatus('JSON downloaded successfully!');
      
      setTimeout(() => setExportStatus(''), 3000);
    } catch (error) {
      setExportStatus('Failed to export JSON');
      setTimeout(() => setExportStatus(''), 3000);
    } finally {
      setIsExporting(false);
    }
  };

  const handleCopyToClipboard = async () => {
    setIsExporting(true);
    setExportStatus('Copying to clipboard...');

    try {
      const csvContent = generateCSV(true);
      await navigator.clipboard.writeText(csvContent);
      setExportStatus('Copied to clipboard!');
      
      setTimeout(() => setExportStatus(''), 3000);
    } catch (error) {
      setExportStatus('Failed to copy to clipboard');
      setTimeout(() => setExportStatus(''), 3000);
    } finally {
      setIsExporting(false);
    }
  };

  const handlePrint = () => {
    const printWindow = window.open('', '_blank');
    if (!printWindow) {
      setExportStatus('Popup blocked. Please allow popups and try again.');
      setTimeout(() => setExportStatus(''), 3000);
      return;
    }

    const timestamp = new Date().toLocaleString();
    const printContent = `
      <!DOCTYPE html>
      <html>
        <head>
          <title>ROI Report - ${timestamp}</title>
          <style>
            body {
              font-family: 'Courier New', monospace;
              margin: 20px;
              background: white;
              color: black;
            }
            h1 {
              text-align: center;
              border-bottom: 2px solid #000;
              padding-bottom: 10px;
            }
            table {
              width: 100%;
              border-collapse: collapse;
              margin-top: 20px;
            }
            th, td {
              border: 1px solid #000;
              padding: 8px;
              text-align: left;
              vertical-align: top;
            }
            th {
              background-color: #f0f0f0;
              font-weight: bold;
            }
            .priority-high { background-color: #ffebee; }
            .priority-medium { background-color: #fff3e0; }
            .priority-low { background-color: #e8f5e8; }
            .contact-prospective { background-color: #e3f2fd; }
            .contact-existing { background-color: #f3e5f5; }
            .summary {
              margin-top: 20px;
              border-top: 2px solid #000;
              padding-top: 20px;
            }
            .summary-item {
              display: inline-block;
              margin-right: 30px;
              text-align: center;
            }
            @media print {
              body { margin: 0; }
              .no-print { display: none; }
            }
          </style>
        </head>
        <body>
          <h1>🎤 ROI Report Analysis</h1>
          <p><strong>Generated:</strong> ${timestamp}</p>
          <p><strong>Total Records:</strong> ${data.length}</p>
          
          <table>
            <thead>
              <tr>
                <th>Name</th>
                <th>Company</th>
                <th>Position</th>
                <th>Discussion</th>
                <th>Contact Type</th>
                <th>Priority</th>
                <th>Action Items</th>
              </tr>
            </thead>
            <tbody>
              ${data.map(item => `
                <tr>
                  <td>${item.name}</td>
                  <td>${item.company}</td>
                  <td>${item.position}</td>
                  <td>${item.discussion}</td>
                  <td class="contact-${item.contactType}">${item.contactType.toUpperCase()}</td>
                  <td class="priority-${item.priorityLevel}">${item.priorityLevel.toUpperCase()}</td>
                  <td>${item.actionItems.join('<br>')}</td>
                </tr>
              `).join('')}
            </tbody>
          </table>

          <div class="summary">
            <h2>Summary Statistics</h2>
            <div class="summary-item">
              <strong>${data.length}</strong><br>Total Contacts
            </div>
            <div class="summary-item">
              <strong>${data.filter(item => item.priorityLevel === 'high').length}</strong><br>High Priority
            </div>
            <div class="summary-item">
              <strong>${data.filter(item => item.priorityLevel === 'medium').length}</strong><br>Medium Priority
            </div>
            <div class="summary-item">
              <strong>${data.filter(item => item.priorityLevel === 'low').length}</strong><br>Low Priority
            </div>
            <div class="summary-item">
              <strong>${data.filter(item => item.contactType === 'prospective').length}</strong><br>Prospective
            </div>
            <div class="summary-item">
              <strong>${data.filter(item => item.contactType === 'existing').length}</strong><br>Existing
            </div>
          </div>
        </body>
      </html>
    `;

    printWindow.document.write(printContent);
    printWindow.document.close();
    printWindow.focus();
    printWindow.print();
  };

  if (data.length === 0) {
    return (
      <div className={`text-center py-6 border border-terminal-cyan/30 rounded-lg ${className}`}>
        <div className="text-2xl mb-2">📤</div>
        <p className="text-terminal-cyan/70">No data available to export</p>
      </div>
    );
  }

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Header */}
      <div className="text-center">
        <h3 className="text-xl font-terminal text-terminal-cyan mb-2 uppercase">
          Export Options
        </h3>
        <p className="text-terminal-cyan/70 text-sm">
          Export your ROI report data in various formats
        </p>
      </div>

      {/* Export Buttons */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* CSV Export */}
        <button
          onClick={handleExportCSV}
          disabled={isExporting}
          className="flex flex-col items-center p-4 border border-terminal-cyan/50 rounded-lg hover:border-terminal-cyan hover:bg-terminal-cyan/5 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <div className="text-2xl mb-2">📊</div>
          <div className="font-terminal text-terminal-cyan text-sm uppercase">Download CSV</div>
          <div className="text-xs text-terminal-cyan/60 mt-1 text-center">
            Excel compatible spreadsheet format
          </div>
        </button>

        {/* JSON Export */}
        <button
          onClick={handleExportJSON}
          disabled={isExporting}
          className="flex flex-col items-center p-4 border border-terminal-cyan/50 rounded-lg hover:border-terminal-cyan hover:bg-terminal-cyan/5 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <div className="text-2xl mb-2">💾</div>
          <div className="font-terminal text-terminal-cyan text-sm uppercase">Download JSON</div>
          <div className="text-xs text-terminal-cyan/60 mt-1 text-center">
            Structured data format for APIs
          </div>
        </button>

        {/* Copy to Clipboard */}
        <button
          onClick={handleCopyToClipboard}
          disabled={isExporting}
          className="flex flex-col items-center p-4 border border-terminal-cyan/50 rounded-lg hover:border-terminal-cyan hover:bg-terminal-cyan/5 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <div className="text-2xl mb-2">📋</div>
          <div className="font-terminal text-terminal-cyan text-sm uppercase">Copy to Clipboard</div>
          <div className="text-xs text-terminal-cyan/60 mt-1 text-center">
            CSV format ready to paste
          </div>
        </button>

        {/* Print */}
        <button
          onClick={handlePrint}
          disabled={isExporting}
          className="flex flex-col items-center p-4 border border-terminal-cyan/50 rounded-lg hover:border-terminal-cyan hover:bg-terminal-cyan/5 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <div className="text-2xl mb-2">🖨️</div>
          <div className="font-terminal text-terminal-cyan text-sm uppercase">Print Report</div>
          <div className="text-xs text-terminal-cyan/60 mt-1 text-center">
            Print-friendly formatted report
          </div>
        </button>
      </div>

      {/* Status Message */}
      {exportStatus && (
        <div className={`
          text-center p-3 rounded border
          ${exportStatus.includes('success') || exportStatus.includes('Copied') 
            ? 'border-terminal-green/50 bg-terminal-green/10 text-terminal-green' 
            : exportStatus.includes('Failed') 
              ? 'border-red-500/50 bg-red-500/10 text-red-400'
              : 'border-terminal-cyan/50 bg-terminal-cyan/10 text-terminal-cyan'
          }
        `}>
          <div className="font-terminal text-sm">
            {exportStatus.includes('success') && '✅ '}
            {exportStatus.includes('Failed') && '❌ '}
            {exportStatus.includes('Generating') && '⚡ '}
            {exportStatus.includes('Copying') && '📋 '}
            {exportStatus}
          </div>
        </div>
      )}

      {/* Export Details */}
      <div className="p-4 border border-terminal-cyan/30 rounded-lg bg-terminal-cyan/5">
        <h4 className="font-terminal text-terminal-cyan mb-3">Export Information</h4>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
          <div>
            <div className="text-terminal-cyan/70 mb-1">Records to export:</div>
            <div className="text-terminal-cyan font-terminal">{data.length} items</div>
          </div>
          <div>
            <div className="text-terminal-cyan/70 mb-1">Generated:</div>
            <div className="text-terminal-cyan font-terminal">
              {new Date().toLocaleString()}
            </div>
          </div>
          <div>
            <div className="text-terminal-cyan/70 mb-1">High priority contacts:</div>
            <div className="text-terminal-cyan font-terminal">
              {data.filter(item => item.priorityLevel === 'high').length}
            </div>
          </div>
          <div>
            <div className="text-terminal-cyan/70 mb-1">Prospective clients:</div>
            <div className="text-terminal-cyan font-terminal">
              {data.filter(item => item.contactType === 'prospective').length}
            </div>
          </div>
        </div>
      </div>

      {/* Export Instructions */}
      <div className="text-xs text-terminal-cyan/60 space-y-1">
        <p>💡 <strong>Export Tips:</strong></p>
        <p>• CSV files can be opened in Excel, Google Sheets, or any spreadsheet application</p>
        <p>• JSON format is ideal for integrating with other systems or APIs</p>
        <p>• Copy to clipboard for quick pasting into emails or documents</p>
        <p>• Print option creates a professional formatted report</p>
      </div>
    </div>
  );
} 
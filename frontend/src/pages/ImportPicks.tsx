import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import '../styles/ImportPicks.css';

const ImportPicks: React.FC = () => {
  const navigate = useNavigate();
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState<{ text: string; type: 'success' | 'error' } | null>(null);
  const [importResults, setImportResults] = useState<any>(null);
  const [previewData, setPreviewData] = useState<string[][] | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selectedFile = e.target.files[0];
      setFile(selectedFile);
      setMessage(null);
      setImportResults(null);
      
      // Read and preview first 5 lines
      const reader = new FileReader();
      reader.onload = (event) => {
        const text = event.target?.result as string;
        const lines = text.split('\n');
        const preview = lines.slice(0, 6).map(line => 
          line.split(',').map(cell => cell.trim())
        );
        setPreviewData(preview);
      };
      reader.readAsText(selectedFile);
    }
  };

  const handleDownloadExample = () => {
    // Create example CSV content
    const exampleData = [
      ['user_id', 'game_id', 'pick_type', 'player_name', 'odds', 'stake'],
      ['1', '123', 'FTD', 'Josh Allen', '+1600', '1.00'],
      ['1', '123', 'ATTS', 'Josh Allen', '+280', '1.00'],
      ['2', '124', 'FTD', 'Derrick Henry', '+800', '1.00'],
      ['2', '125', 'ATTS', 'Christian McCaffrey', '+180', '1.00']
    ];

    // Convert to CSV string
    const csvContent = exampleData.map(row => row.join(','));
    const csvString = csvContent.join('\n');

    // Create blob and download
    const blob = new Blob([csvString], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    
    link.setAttribute('href', url);
    link.setAttribute('download', 'picks_import_example.csv');
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleUpload = async () => {
    if (!file) {
      setMessage({ text: 'Please select a CSV file to upload', type: 'error' });
      return;
    }

    setUploading(true);
    setMessage(null);
    setImportResults(null);

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch('http://localhost:5000/api/import-picks', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Failed to import picks');
      }

      setMessage({ 
        text: `Successfully imported ${data.imported_count} picks!`, 
        type: 'success' 
      });
      setImportResults(data);
      setFile(null);
      
      // Reset file input
      const fileInput = document.getElementById('csvFile') as HTMLInputElement;
      if (fileInput) fileInput.value = '';
      
    } catch (err) {
      setMessage({ 
        text: err instanceof Error ? err.message : 'Failed to import picks', 
        type: 'error' 
      });
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="import-picks-container">
      <div className="import-picks-header">
        <h1>📥 Import Picks</h1>
        <button onClick={() => navigate('/admin')} className="btn-back">
          ← Back to Admin
        </button>
      </div>

      <div className="import-instructions">
        <h2>Instructions</h2>
        <ol>
          <li>Download the example CSV file to see the required format</li>
          <li>Prepare your CSV file with the following columns:
            <ul>
              <li><strong>user_id</strong>: The ID of the user making the pick</li>
              <li><strong>game_id</strong>: The ID of the game</li>
              <li><strong>pick_type</strong>: Either 'FTD' or 'ATTS'</li>
              <li><strong>player_name</strong>: Full name of the player</li>
              <li><strong>odds</strong>: Odds in American format (e.g., +1600, -110)</li>
              <li><strong>stake</strong>: Amount wagered (default 1.00)</li>
            </ul>
          </li>
          <li>Upload your CSV file and click "Import Picks"</li>
        </ol>
        
        <button onClick={handleDownloadExample} className="btn-download-example">
          ⬇️ Download Example CSV
        </button>
      </div>

      {message && (
        <div className={`message ${message.type}`}>
          {message.text}
        </div>
      )}

      <div className="upload-section">
        <h2>Upload CSV File</h2>
        <div className="file-input-wrapper">
          <input
            type="file"
            id="csvFile"
            accept=".csv"
            onChange={handleFileChange}
            disabled={uploading}
          />
          {file && <span className="file-name">Selected: {file.name}</span>}
        </div>

        <button
          onClick={handleUpload}
          disabled={!file || uploading}
          className="btn-upload"
        >
          {uploading ? 'Importing...' : 'Import Picks'}
        </button>
      </div>

      {previewData && previewData.length > 1 && (
        <div className="csv-preview">
          <h2>Preview (First 5 Rows)</h2>
          <div className="preview-table-wrapper">
            <table className="preview-table">
              <thead>
                <tr>
                  {previewData[0].map((header, idx) => (
                    <th key={idx}>{header}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {previewData.slice(1, 6).map((row, rowIdx) => (
                  <tr key={rowIdx}>
                    {row.map((cell, cellIdx) => (
                      <td key={cellIdx}>{cell}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {importResults && (
        <div className="import-results">
          <h2>Import Results</h2>
          <div className="results-grid">
            <div className="result-card">
              <div className="result-label">Total Imported</div>
              <div className="result-value">{importResults.imported_count}</div>
            </div>
            {importResults.skipped_count > 0 && (
              <div className="result-card warning">
                <div className="result-label">Skipped (Duplicates)</div>
                <div className="result-value">{importResults.skipped_count}</div>
              </div>
            )}
            {importResults.errors && importResults.errors.length > 0 && (
              <div className="result-card error">
                <div className="result-label">Errors</div>
                <div className="result-value">{importResults.errors.length}</div>
              </div>
            )}
          </div>

          {importResults.errors && importResults.errors.length > 0 && (
            <div className="error-details">
              <h3>Errors:</h3>
              <ul>
                {importResults.errors.map((error: string, idx: number) => (
                  <li key={idx}>{error}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default ImportPicks;

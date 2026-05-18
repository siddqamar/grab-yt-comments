import React, { useState } from 'react';
import { IconYoutube, IconSearch, IconTerminal } from './components/Icons';
import ConfigPanel from './components/ConfigPanel';
import Dashboard from './components/Dashboard';
import { fetchComments, downloadData } from './services/apiService';
import { ProcessingState, Comment, AnalysisStats, ExportFormat } from './types';

function App() {
  const [url, setUrl] = useState('');
  const [enableClassification, setEnableClassification] = useState(false);
  const [exportFormat, setExportFormat] = useState<ExportFormat>('JSON');
  
  const [processingState, setProcessingState] = useState<ProcessingState>({ status: 'IDLE' });
  const [results, setResults] = useState<{ comments: Comment[], stats: AnalysisStats } | null>(null);

  const handleProcess = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url) return;

    setProcessingState({ status: 'LOADING' });
    setResults(null);

    try {
      const data = await fetchComments(url, enableClassification);
      setResults(data);
      setProcessingState({ status: 'COMPLETE' });
    } catch (err: any) {
      setProcessingState({ status: 'ERROR', error: err.message || 'Unknown error occurred' });
    }
  };

  const handleDownload = () => {
    if (results) {
      downloadData(results.comments, exportFormat);
    }
  };

  const handleReset = () => {
    setResults(null);
    setProcessingState({ status: 'IDLE' });
    setUrl('');
  };

  return (
    <div className="min-h-screen w-full bg-void text-gray-200 selection:bg-acid selection:text-black font-sans pb-20">
      
      {/* Header / Nav */}
      <nav className="w-full border-b border-subtle bg-void/80 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2" onClick={handleReset} role="button">
            <div className="w-8 h-8 bg-acid rounded-md flex items-center justify-center">
              <IconTerminal className="text-black w-5 h-5" />
            </div>
            <span className="font-bold text-xl tracking-tight text-white">Comment<span className="text-acid">Flux</span></span>
          </div>
          <div className="flex items-center gap-4">
             <span className="text-xs font-mono text-gray-500 hidden sm:block">Open-Source</span>
             <a href="#" className="text-xs font-mono border border-subtle px-3 py-1 rounded-full hover:border-gray-400 transition-colors">Project</a>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="px-6 pt-16 flex flex-col items-center">
        
        {/* Hero Section */}
        <div className={`transition-all duration-700 ease-in-out w-full flex flex-col items-center ${results ? 'translate-y-0' : 'translate-y-[10vh]'}`}>
          
          <div className="text-center max-w-2xl mx-auto mb-10">
            <h1 className="text-5xl md:text-7xl font-bold mb-6 tracking-tighter text-white">
              Extract. <span className="text-transparent bg-clip-text bg-gradient-to-r from-acid to-emerald-400">Classify.</span> Export.
            </h1>
            <p className="text-lg text-gray-400 font-light max-w-lg mx-auto">
              Professional grade YouTube comment extraction powered by Python. 
              Analyze comment categories instantly.
            </p>
          </div>

          {/* Input Form */}
          <form onSubmit={handleProcess} className="w-full max-w-2xl relative group z-10">
            <div className="absolute -inset-1 bg-gradient-to-r from-acid to-lavender rounded-xl blur opacity-25 group-hover:opacity-50 transition duration-1000 group-hover:duration-200"></div>
            <div className="relative flex items-center bg-surface border border-subtle rounded-xl p-2 shadow-2xl">
              <div className="pl-4 pr-3 text-gray-500">
                <IconYoutube />
              </div>
              <input 
                type="text" 
                placeholder="Paste YouTube URL here..." 
                className="flex-1 bg-transparent border-none outline-none text-white placeholder-gray-600 font-mono text-sm h-12"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                disabled={processingState.status === 'LOADING'}
              />
              <button 
                type="submit"
                disabled={!url || processingState.status === 'LOADING'}
                className="bg-white text-black hover:bg-acid disabled:bg-gray-800 disabled:text-gray-600 disabled:cursor-not-allowed px-6 py-3 rounded-lg font-bold transition-all duration-300 flex items-center gap-2"
              >
                {processingState.status === 'LOADING' ? (
                   <span className="animate-pulse">Processing...</span>
                ) : (
                  <>
                    <span>Run</span>
                    <IconSearch size={16} />
                  </>
                )}
              </button>
            </div>
            {processingState.status === 'ERROR' && (
              <div className="absolute top-full mt-2 left-0 text-red-500 text-xs font-mono flex items-center gap-1">
                <span>⚠ {processingState.error}</span>
              </div>
            )}
          </form>

          {/* Config Panel - Hide if results shown to reduce clutter, or keep accessible */}
          {!results && (
             <ConfigPanel 
               enableClassification={enableClassification}
               setEnableClassification={setEnableClassification}
               exportFormat={exportFormat}
               setExportFormat={setExportFormat}
               disabled={processingState.status === 'LOADING'}
             />
          )}

        </div>

        {/* Results Section */}
        {results && processingState.status === 'COMPLETE' && (
          <Dashboard 
            comments={results.comments} 
            stats={results.stats} 
            onDownload={handleDownload}
            format={exportFormat}
            isClassified={enableClassification}
          />
        )}

      </main>
    </div>
  );
}

export default App;

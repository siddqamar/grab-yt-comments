import React, { useEffect, useState } from 'react';
import { IconYoutube, IconSearch, IconTerminal, IconAlert, IconCheck } from './components/Icons';
import ConfigPanel from './components/ConfigPanel';
import Dashboard from './components/Dashboard';
import { fetchComments, fetchReadiness, downloadData } from './services/apiService';
import {
  ProcessingState,
  Comment,
  AnalysisStats,
  ExportFormat,
  AppReadiness,
  UserNotice,
} from './types';

function App() {
  const [url, setUrl] = useState('');
  const [enableClassification, setEnableClassification] = useState(false);
  const [exportFormat, setExportFormat] = useState<ExportFormat>('JSON');
  const [processingState, setProcessingState] = useState<ProcessingState>({ status: 'IDLE' });
  const [results, setResults] = useState<{ comments: Comment[]; stats: AnalysisStats } | null>(
    null
  );
  const [notice, setNotice] = useState<UserNotice | null>(null);
  const [readiness, setReadiness] = useState<AppReadiness | null>(null);
  const [isReadinessLoading, setIsReadinessLoading] = useState(true);
  const [readinessError, setReadinessError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    const loadInitialReadiness = async () => {
      setIsReadinessLoading(true);
      setReadinessError(null);

      try {
        const readinessData = await fetchReadiness();
        if (!cancelled) {
          setReadiness(readinessData);
        }
      } catch (error) {
        if (!cancelled) {
          setReadiness(null);
          setReadinessError(
            error instanceof Error ? error.message : 'Unable to load readiness state.'
          );
        }
      } finally {
        if (!cancelled) {
          setIsReadinessLoading(false);
        }
      }
    };

    void loadInitialReadiness();

    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (readiness && !readiness.classificationAvailable && enableClassification) {
      setEnableClassification(false);
    }
  }, [enableClassification, readiness]);

  const refreshReadiness = async () => {
    setIsReadinessLoading(true);
    setReadinessError(null);

    try {
      const readinessData = await fetchReadiness();
      setReadiness(readinessData);
    } catch (error) {
      setReadiness(null);
      setReadinessError(error instanceof Error ? error.message : 'Unable to load readiness state.');
    } finally {
      setIsReadinessLoading(false);
    }
  };

  const backendUnavailable = Boolean(readinessError);
  const missingApiKey = readiness ? !readiness.youtubeConfigured : false;
  const classificationUnavailable = readiness ? !readiness.classificationAvailable : false;
  const classificationHint = classificationUnavailable
    ? readiness?.classificationMessage || 'Classification is unavailable right now.'
    : 'Classify comments using Python backend';
  const runDisabled =
    !url ||
    processingState.status === 'LOADING' ||
    isReadinessLoading ||
    backendUnavailable ||
    missingApiKey;

  const handleProcess = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url || runDisabled) return;

    setProcessingState({ status: 'LOADING' });
    setResults(null);
    setNotice(null);

    try {
      const data = await fetchComments(url, enableClassification);
      setResults({ comments: data.comments, stats: data.stats });
      setNotice(data.notice || null);
      setProcessingState({ status: 'COMPLETE' });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unknown error occurred';
      setProcessingState({ status: 'ERROR', error: message });
    }
  };

  const handleDownload = () => {
    if (results) {
      downloadData(results.comments, exportFormat);
    }
  };

  const handleReset = () => {
    setResults(null);
    setNotice(null);
    setProcessingState({ status: 'IDLE' });
    setUrl('');
  };

  const statusCards = [
    {
      label: 'Backend',
      ok: !backendUnavailable,
      state: backendUnavailable ? 'Unavailable' : 'Ready',
      message: backendUnavailable
        ? readinessError || 'Backend unavailable.'
        : readiness?.backendMessage || 'Checking backend readiness...',
    },
    {
      label: 'YouTube API',
      ok: readiness ? readiness.youtubeConfigured : false,
      state: readiness ? (readiness.youtubeConfigured ? 'Configured' : 'Missing') : 'Checking',
      message: readiness?.youtubeMessage || 'Waiting for backend readiness...',
    },
    {
      label: 'Model Server',
      ok: readiness ? readiness.classificationAvailable : false,
      state: readiness ? (readiness.classificationAvailable ? 'Available' : 'Unavailable') : 'Checking',
      message: readiness?.classificationMessage || 'Waiting for backend readiness...',
    },
  ];
  const isClassifiedResult = Boolean(
    results?.comments.some((comment) => Boolean(comment.classification))
  );

  return (
    <div className="min-h-screen w-full bg-void text-gray-200 selection:bg-acid selection:text-black font-sans pb-20">
      <nav className="w-full border-b border-subtle bg-void/80 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2" onClick={handleReset} role="button">
            <div className="w-8 h-8 bg-acid rounded-md flex items-center justify-center">
              <IconTerminal className="text-black w-5 h-5" />
            </div>
            <span className="font-bold text-xl tracking-tight text-white">
              Grab<span className="text-acid">Comment</span>
            </span>
          </div>
          <div className="flex items-center gap-4">
            <span className="text-xs font-mono text-gray-500 hidden sm:block">Open-Source</span>
            <a
              href="#"
              className="text-xs font-mono border border-subtle px-3 py-1 rounded-full hover:border-gray-400 transition-colors"
            >
              Project
            </a>
          </div>
        </div>
      </nav>

      <main className="px-6 pt-16 flex flex-col items-center">
        <div
          className={`transition-all duration-700 ease-in-out w-full flex flex-col items-center ${
            results ? 'translate-y-0' : 'translate-y-[10vh]'
          }`}
        >
          <div className="text-center max-w-2xl mx-auto mb-10">
            <h1 className="text-5xl md:text-7xl font-bold mb-6 tracking-tighter text-white">
              Extract.{' '}
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-acid to-emerald-400">
                Classify.
              </span>{' '}
              Export.
            </h1>
            <p className="text-lg text-gray-400 font-light max-w-lg mx-auto">
              Professional grade YouTube comment extraction powered by Python. Analyze comment
              categories instantly.
            </p>
          </div>

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
                disabled={runDisabled}
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
                <span>{processingState.error}</span>
              </div>
            )}
          </form>

          <div className="w-full max-w-2xl mt-6">
            <div className="flex items-center justify-between mb-3 gap-4">
              <div>
                <p className="text-xs font-mono uppercase tracking-[0.3em] text-gray-500">
                  Runtime Readiness
                </p>
                <p className="text-sm text-gray-400">
                  Desktop startup depends on the backend, the YouTube API key, and the optional
                  model server.
                </p>
              </div>
              <button
                type="button"
                onClick={() => void refreshReadiness()}
                disabled={isReadinessLoading}
                className="border border-subtle px-3 py-2 rounded-full text-xs font-mono text-gray-300 hover:border-gray-400 disabled:text-gray-600 disabled:cursor-not-allowed"
              >
                {isReadinessLoading ? 'Checking...' : 'Refresh Status'}
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              {statusCards.map((card) => (
                <div
                  key={card.label}
                  className={`rounded-xl border p-4 text-left ${
                    card.ok ? 'border-emerald-500/30 bg-emerald-500/5' : 'border-amber-500/30 bg-amber-500/5'
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-mono uppercase tracking-wider text-gray-400">
                      {card.label}
                    </span>
                    {card.ok ? (
                      <IconCheck className="text-emerald-400" size={16} />
                    ) : (
                      <IconAlert className="text-amber-300" size={16} />
                    )}
                  </div>
                  <p className="text-sm font-bold text-white">{card.state}</p>
                  <p className="text-xs text-gray-400 mt-2">{card.message}</p>
                </div>
              ))}
            </div>
          </div>

          {notice && (
            <div className="w-full max-w-2xl mt-4 rounded-xl border border-amber-500/30 bg-amber-500/10 p-4 text-left">
              <p className="text-xs font-mono uppercase tracking-wider text-amber-200">
                Classification Notice
              </p>
              <p className="text-sm text-amber-50 mt-2">{notice.message}</p>
            </div>
          )}

          {!results && (
            <ConfigPanel
              enableClassification={enableClassification}
              setEnableClassification={setEnableClassification}
              exportFormat={exportFormat}
              setExportFormat={setExportFormat}
              disabled={processingState.status === 'LOADING'}
              classificationDisabled={classificationUnavailable}
              classificationHint={classificationHint}
            />
          )}
        </div>

        {results && processingState.status === 'COMPLETE' && (
          <Dashboard
            comments={results.comments}
            stats={results.stats}
            onDownload={handleDownload}
            format={exportFormat}
            isClassified={isClassifiedResult}
          />
        )}
      </main>
    </div>
  );
}

export default App;

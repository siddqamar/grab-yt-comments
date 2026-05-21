import React from 'react';
import { ExportFormat } from '../types';
import { IconCpu, IconJson, IconCsv } from './Icons';

interface ConfigPanelProps {
  enableClassification: boolean;
  setEnableClassification: (val: boolean) => void;
  exportFormat: ExportFormat;
  setExportFormat: (val: ExportFormat) => void;
  disabled?: boolean;
}

const ConfigPanel: React.FC<ConfigPanelProps> = ({
  enableClassification,
  setEnableClassification,
  exportFormat,
  setExportFormat,
  disabled
}) => {
  return (
    <div className="flex flex-col md:flex-row gap-6 w-full max-w-2xl mx-auto mt-8 p-6 border border-subtle bg-surface/50 rounded-xl backdrop-blur-sm">
      
      {/* Classification Toggle */}
      <div className="flex-1 flex flex-col gap-3">
        <div className="flex items-center gap-2 text-sm font-mono text-gray-400 uppercase tracking-wider">
          <IconCpu size={16} />
          <span>AI Processing</span>
        </div>
        <label className={`relative flex items-center p-4 border rounded-lg cursor-pointer transition-all duration-300 ${enableClassification ? 'border-acid bg-acid/5' : 'border-subtle hover:border-gray-500'}`}>
          <input 
            type="checkbox"
            className="sr-only"
            checked={enableClassification}
            onChange={(e) => setEnableClassification(e.target.checked)}
            disabled={disabled}
          />
          <div className="flex-1">
            <span className={`block font-bold ${enableClassification ? 'text-acid' : 'text-gray-300'}`}>
              Comment Classification
            </span>
            <span className="text-xs text-gray-500">Classify comments using Python backend</span>
          </div>
          <div className={`w-5 h-5 rounded-full border flex items-center justify-center ${enableClassification ? 'border-acid bg-acid' : 'border-gray-600'}`}>
             {enableClassification && <div className="w-2 h-2 rounded-full bg-black" />}
          </div>
        </label>
      </div>

      {/* Format Selection */}
      <div className="flex-1 flex flex-col gap-3">
        <div className="flex items-center gap-2 text-sm font-mono text-gray-400 uppercase tracking-wider">
          <IconJson size={16} />
          <span>Export Format</span>
        </div>
        <div className="flex gap-3 h-full">
          <button
            onClick={() => setExportFormat('JSON')}
            disabled={disabled}
            className={`flex-1 flex flex-col items-center justify-center gap-2 p-2 rounded-lg border transition-all ${exportFormat === 'JSON' ? 'border-lavender bg-lavender/10 text-lavender' : 'border-subtle text-gray-500 hover:border-gray-500'}`}
          >
            <IconJson size={20} />
            <span className="text-xs font-mono font-bold">JSON</span>
          </button>
          <button
            onClick={() => setExportFormat('CSV')}
            disabled={disabled}
            className={`flex-1 flex flex-col items-center justify-center gap-2 p-2 rounded-lg border transition-all ${exportFormat === 'CSV' ? 'border-lavender bg-lavender/10 text-lavender' : 'border-subtle text-gray-500 hover:border-gray-500'}`}
          >
            <IconCsv size={20} />
            <span className="text-xs font-mono font-bold">CSV</span>
          </button>
        </div>
      </div>

    </div>
  );
};

export default ConfigPanel;

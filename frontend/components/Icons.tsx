import React from 'react';
import { 
  Terminal, 
  Download, 
  Activity, 
  MessageSquare, 
  Search, 
  CheckCircle, 
  AlertCircle,
  FileJson,
  FileSpreadsheet,
  Cpu,
  Zap,
  Youtube
} from 'lucide-react';

interface IconProps {
  className?: string;
  size?: number | string;
}

export const IconTerminal = ({ className, size }: IconProps) => <Terminal className={className} size={size} />;
export const IconDownload = ({ className, size }: IconProps) => <Download className={className} size={size} />;
export const IconActivity = ({ className, size }: IconProps) => <Activity className={className} size={size} />;
export const IconMessage = ({ className, size }: IconProps) => <MessageSquare className={className} size={size} />;
export const IconSearch = ({ className, size }: IconProps) => <Search className={className} size={size} />;
export const IconCheck = ({ className, size }: IconProps) => <CheckCircle className={className} size={size} />;
export const IconAlert = ({ className, size }: IconProps) => <AlertCircle className={className} size={size} />;
export const IconJson = ({ className, size }: IconProps) => <FileJson className={className} size={size} />;
export const IconCsv = ({ className, size }: IconProps) => <FileSpreadsheet className={className} size={size} />;
export const IconCpu = ({ className, size }: IconProps) => <Cpu className={className} size={size} />;
export const IconZap = ({ className, size }: IconProps) => <Zap className={className} size={size} />;
export const IconYoutube = ({ className, size }: IconProps) => <Youtube className={className} size={size} />;
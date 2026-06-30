import React from 'react';
import { Comment, AnalysisStats, ExportFormat } from '../types';
import { Badge } from './ui/Badge';
import { IconDownload, IconMessage, IconActivity, IconZap } from './Icons';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';
import { CATEGORY_COLORS } from '../constants';

interface DashboardProps {
  comments: Comment[];
  stats: AnalysisStats;
  onDownload: () => void;
  format: ExportFormat;
  isClassified: boolean;
}

const Dashboard: React.FC<DashboardProps> = ({ comments, stats, onDownload, format, isClassified }) => {
  
  const chartData = [
    { name: 'Appreciation', value: stats.appreciation, color: CATEGORY_COLORS.appreciation },
    { name: 'Humor', value: stats.humor, color: CATEGORY_COLORS.humor },
    { name: 'Questions', value: stats.questions, color: CATEGORY_COLORS.questions },
    { name: 'Criticism', value: stats.criticism, color: CATEGORY_COLORS.criticism },
    { name: 'Personal Experience', value: stats.personalExperience, color: CATEGORY_COLORS['personal experience'] },
    { name: 'Feedback', value: stats.feedback, color: CATEGORY_COLORS.feedback },
    { name: 'Spam', value: stats.spam, color: CATEGORY_COLORS.spam },
  ].filter(d => d.value > 0);

  return (
    <div className="w-full max-w-6xl mx-auto mt-12 animate-fade-in-up">
      
      {/* Action Bar */}
      <div className="flex justify-between items-end mb-6 border-b border-subtle pb-4">
        <div>
          <h2 className="text-3xl font-bold font-sans tracking-tight">Results Interface</h2>
          <p className="text-gray-500 font-mono text-sm mt-1">
            Processed {stats.total} comments via Python API
          </p>
        </div>
        <button 
          onClick={onDownload}
          className="group flex items-center gap-2 bg-white text-black px-6 py-3 rounded-full font-bold hover:bg-acid hover:scale-105 transition-all duration-300"
        >
          <IconDownload className="w-4 h-4 group-hover:animate-bounce" />
          <span>Download .{format.toLowerCase()}</span>
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Stats Column (Only if classified) */}
        {isClassified && (
          <div className="lg:col-span-1 flex flex-col gap-6">
            {/* Chart Card */}
            <div className="bg-surface border border-subtle p-6 rounded-2xl relative overflow-hidden">
               <div className="absolute top-0 right-0 p-4 opacity-20">
                 <IconActivity size={48} />
               </div>
               <h3 className="font-mono text-gray-400 text-xs uppercase tracking-widest mb-4">Category Distribution</h3>
               
               <div className="h-48 w-full">
                 <ResponsiveContainer width="100%" height="100%">
                   <PieChart>
                     <Pie
                       data={chartData}
                       cx="50%"
                       cy="50%"
                       innerRadius={40}
                       outerRadius={70}
                       paddingAngle={5}
                       dataKey="value"
                       stroke="none"
                     >
                       {chartData.map((entry, index) => (
                         <Cell key={`cell-${index}`} fill={entry.color} />
                       ))}
                     </Pie>
                     <Tooltip 
                        contentStyle={{ backgroundColor: '#121212', borderColor: '#333', borderRadius: '8px', fontFamily: 'JetBrains Mono', fontSize: '12px' }}
                        itemStyle={{ color: '#fff' }}
                     />
                   </PieChart>
                 </ResponsiveContainer>
               </div>
               
               <div className="grid grid-cols-2 gap-2 mt-4">
                 {chartData.map(d => (
                   <div key={d.name} className="flex items-center gap-2 text-xs font-mono">
                     <span className="w-2 h-2 rounded-full" style={{ backgroundColor: d.color }}></span>
                     <span className="text-gray-300">{d.name}</span>
                     <span className="ml-auto font-bold">{d.value}</span>
                   </div>
                 ))}
               </div>
            </div>

            {/* Quick Stats */}
            <div className="bg-surface border border-subtle p-6 rounded-2xl flex flex-col justify-center items-center text-center">
              <IconZap className="text-acid mb-2" size={32} />
              <div className="text-4xl font-bold font-sans text-white">{stats.questions + stats.feedback}</div>
              <div className="text-xs font-mono text-gray-500 uppercase mt-1">Actionable Comments</div>
            </div>
          </div>
        )}

        {/* Comments List */}
        <div className={`${isClassified ? 'lg:col-span-2' : 'lg:col-span-3'} bg-surface border border-subtle rounded-2xl flex flex-col h-[600px]`}>
          <div className="p-4 border-b border-subtle flex items-center justify-between bg-void/50 rounded-t-2xl">
            <div className="flex items-center gap-2">
              <IconMessage className="text-gray-400" size={18} />
              <span className="font-mono text-xs font-bold text-gray-300 uppercase">Live Feed</span>
            </div>
            <span className="text-xs font-mono text-gray-600">{stats.total} items</span>
          </div>
          
          <div className="flex-1 overflow-y-auto p-4 space-y-3">
            {comments.map((comment) => (
              <div key={comment.id} className="p-4 rounded-xl bg-void border border-subtle hover:border-gray-600 transition-colors group">
                <div className="flex justify-between items-start mb-2">
                  <div className="flex items-center gap-2">
                    <div className="w-6 h-6 rounded-full bg-gradient-to-tr from-gray-700 to-gray-600 flex items-center justify-center text-[10px] font-bold">
                      {comment.author.charAt(0)}
                    </div>
                    <span className="text-xs font-bold text-gray-300">{comment.author}</span>
                    <span className="text-[10px] text-gray-600 font-mono">{new Date(comment.timestamp).toLocaleDateString()}</span>
                  </div>
                  {isClassified && comment.classification && (
                    <Badge status={comment.classification} />
                  )}
                </div>
                <p className="text-sm text-gray-300 leading-relaxed font-sans">{comment.text}</p>
                <div className="mt-3 flex items-center gap-4 text-xs text-gray-600 font-mono">
                  <span>♥ {comment.likes}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

      </div>
    </div>
  );
};

export default Dashboard;

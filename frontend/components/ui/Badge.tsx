import React from 'react';
import { ClassificationStatus } from '../../types';

interface BadgeProps {
  status: ClassificationStatus;
  className?: string;
}

export const Badge: React.FC<BadgeProps> = ({ status, className = '' }) => {
  const getStyle = () => {
    switch (status) {
      case ClassificationStatus.Appreciation:
        return 'border-acid text-acid bg-acid/10';
      case ClassificationStatus.Humor:
        return 'border-sky-400 text-sky-400 bg-sky-400/10';
      case ClassificationStatus.Questions:
        return 'border-yellow-400 text-yellow-400 bg-yellow-400/10';
      case ClassificationStatus.Criticism:
        return 'border-red-500 text-red-500 bg-red-500/10';
      case ClassificationStatus.PersonalExperience:
        return 'border-orange-400 text-orange-400 bg-orange-400/10';
      case ClassificationStatus.Feedback:
        return 'border-lavender text-lavender bg-lavender/10';
      case ClassificationStatus.Spam:
        return 'border-pink-400 text-pink-400 bg-pink-400/10';
      default:
        return 'border-white text-white bg-white/10';
    }
  };

  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-mono font-medium border ${getStyle()} ${className}`}>
      {status}
    </span>
  );
};

import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { Badge } from '../components/ui/Badge';
import { ClassificationStatus } from '../types';

describe('Badge', () => {
  it('renders the status text', () => {
    render(<Badge status={ClassificationStatus.Questions} />);
    expect(screen.getByText('questions')).toBeInTheDocument();
  });

  it('applies different styles for different statuses', () => {
    const { rerender } = render(<Badge status={ClassificationStatus.Appreciation} />);
    const badge = screen.getByText('appreciation');
    expect(badge.className).toContain('border-acid');

    rerender(<Badge status={ClassificationStatus.Spam} />);
    expect(screen.getByText('spam').className).toContain('border-pink');
  });
});

import React, { useState, useRef, useEffect } from 'react';
import { Loader2, CheckCircle2, AlertCircle } from 'lucide-react';
import type { CategoryKey } from './design-tokens';

interface ActionButtonProps {
  onClick: () => unknown | Promise<unknown>;
  text: string;
  category?: CategoryKey;
  variant?: 'primary' | 'secondary';
  colorClass?: string; // keeping for backward compatibility in parts not yet refactored
  isLoading?: boolean;
  disabled?: boolean;
  title?: string;
  requiresConfirm?: boolean;
}

export const ActionButton: React.FC<ActionButtonProps> = ({ 
  onClick, 
  text, 
  variant = 'primary',
  isLoading = false,
  disabled = false,
  title,
  requiresConfirm = false
}) => {
  const [internalStatus, setInternalStatus] = useState<'idle' | 'confirming' | 'loading' | 'success' | 'error'>('idle');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    return () => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
    };
  }, []);

  const handleClick = async () => {
    if (disabled || isLoading || internalStatus === 'loading') return;

    if (requiresConfirm && internalStatus !== 'confirming') {
      setInternalStatus('confirming');
      timeoutRef.current = setTimeout(() => {
        setInternalStatus('idle');
      }, 3000);
      return;
    }

    if (timeoutRef.current) clearTimeout(timeoutRef.current);
    
    // Proceed to execute
    setInternalStatus('loading');
    setErrorMessage(null);

    try {
      const result = await onClick();
      setInternalStatus(result === false ? 'error' : result === true ? 'success' : 'idle');
      timeoutRef.current = setTimeout(() => setInternalStatus('idle'), 2000);
    } catch (err: any) {
      setInternalStatus('error');
      setErrorMessage(err.message || 'Action failed');
      setTimeout(() => setInternalStatus('idle'), 3000);
    }
  };

  const isActuallyLoading = isLoading || internalStatus === 'loading';
  const isDisabled = disabled || isActuallyLoading;

  let displayText = text;
  if (internalStatus === 'confirming') displayText = 'Click again to confirm';
  else if (internalStatus === 'loading' || isLoading) displayText = 'Processing...';
  else if (internalStatus === 'success') displayText = 'Success!';
  else if (internalStatus === 'error') displayText = errorMessage || 'Failed';

  return (
    <button 
      onClick={handleClick}
      disabled={isDisabled}
      title={title}
      className={`action-button ${variant==='secondary'?'secondary-button':'primary-button'} action-${internalStatus}`}
    >
      {isActuallyLoading && <Loader2 size={14} className="animate-spin" />}
      {internalStatus === 'success' && <CheckCircle2 size={16} />}
      {internalStatus === 'error' && <AlertCircle size={16} />}
      {displayText}
    </button>
  );
};

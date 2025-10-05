import { useState, useCallback } from 'react';

interface ToastState {
  id: number;
  message: string;
  type: 'success' | 'error' | 'info';
}

export function useToast() {
  const [toasts, setToasts] = useState<ToastState[]>([]);
  const [nextId, setNextId] = useState(0);

  const showToast = useCallback((message: string, type: 'success' | 'error' | 'info') => {
    const id = nextId;
    setNextId(id + 1);
    setToasts(prev => [...prev, { id, message, type }]);
  }, [nextId]);

  const removeToast = useCallback((id: number) => {
    setToasts(prev => prev.filter(toast => toast.id !== id));
  }, []);

  return {
    toasts,
    showToast,
    removeToast,
  };
}

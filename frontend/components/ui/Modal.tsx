'use client';

import { useRouter } from 'next/navigation';
import { useEffect, useRef, ReactNode } from 'react';
import { X } from 'lucide-react';

interface ModalProps {
  children: ReactNode;
}

export function Modal({ children }: ModalProps) {
  const router = useRouter();
  const dialogRef = useRef<HTMLDialogElement>(null);

  useEffect(() => {
    const dialog = dialogRef.current;
    if (dialog) {
      dialog.showModal();
    }
    
    return () => {
      if (dialog) {
        dialog.close();
      }
    };
  }, []);

  const closeModal = () => {
    router.back();
  };

  const handleBackdropClick = (e: React.MouseEvent<HTMLDialogElement>) => {
    if (e.target === e.currentTarget) {
      closeModal();
    }
  };

  return (
    <dialog
      ref={dialogRef}
      className="backdrop:bg-black/50 bg-transparent p-0 max-w-4xl w-full max-h-[90vh] rounded-lg"
      onClick={handleBackdropClick}
      onClose={closeModal}
    >
      <div className="relative bg-white rounded-lg shadow-xl max-h-[90vh] overflow-hidden">
        {/* 閉じるボタン */}
        <button
          onClick={closeModal}
          className="absolute top-4 right-4 z-50 bg-black/20 hover:bg-black/40 text-white rounded-full p-2 transition-colors"
          aria-label="モーダルを閉じる"
        >
          <X className="w-5 h-5" />
        </button>
        
        {/* モーダルコンテンツ */}
        <div className="overflow-y-auto max-h-[90vh]">
          {children}
        </div>
      </div>
    </dialog>
  );
}
import React, { type ReactNode } from 'react';

interface ModalProps {
  title?: string;
  onClose: () => void;
  children: ReactNode;
}

export const Modal: React.FC<ModalProps> = ({ title, onClose, children }) => {
  return (
    <div className="fixed inset-0 flex items-center justify-center bg-black/40 backdrop-blur-sm z-50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg max-h-[90vh] overflow-y-auto relative flex flex-col">
        {title && (
          <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100 sticky top-0 bg-white rounded-t-2xl z-10">
            <h3 className="text-xl font-bold text-slate-800">{title}</h3>
            <button
              onClick={onClose}
              className="w-8 h-8 flex items-center justify-center rounded-full bg-gray-100 hover:bg-gray-200 text-gray-600 hover:text-gray-900 text-xl leading-none transition"
              aria-label="Close modal"
            >
              &times;
            </button>
          </div>
        )}
        <div className="p-6 flex-1">{children}</div>
      </div>
    </div>
  );
};

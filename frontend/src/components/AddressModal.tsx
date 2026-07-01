import React, { useState } from 'react';
import { Modal } from './Modal';
import { LocationPicker } from './LocationPicker';
import api from '../services/api';

interface AddressModalProps {
  isOpen: boolean;
  onClose: () => void;
  onCreated: () => void;
}

export const AddressModal: React.FC<AddressModalProps> = ({ isOpen, onClose, onCreated }) => {
  const [name, setName] = useState('');
  const [position, setPosition] = useState<{ lat: number; lng: number } | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async () => {
    if (!name || !position) return;
    setLoading(true);
    setError('');
    try {
      // Round to 6 decimal places to satisfy DecimalField(max_digits=12, decimal_places=6)
      const response = await api.post('stores/addresses/', {
        name,
        latitude: parseFloat(position.lat.toFixed(6)),
        longitude: parseFloat(position.lng.toFixed(6)),
      });
      // Auto-activate the new address on the server
      await api.post(`stores/addresses/${response.data.id}/set-active/`);
      onCreated();
      setName('');
      setPosition(null);
      onClose();
    } catch (err: any) {
      console.error('Failed to create address', err);
      const data = err.response?.data;
      if (data) {
        // Show field-level errors
        const msgs = Object.values(data).flat().join(' | ');
        setError(msgs || 'خطا در ذخیره آدرس');
      } else {
        setError('خطا در ذخیره آدرس. لطفا دوباره تلاش کنید.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleMapSelect = (lat: number, lng: number) => {
    setPosition({ lat, lng });
  };

  if (!isOpen) return null;

  return (
    <Modal onClose={onClose} title="ایجاد آدرس جدید">
      <div className="space-y-5">
        {/* Address name input */}
        <div>
          <label className="block text-sm font-semibold text-slate-700 mb-1">نام آدرس</label>
          <input
            type="text"
            placeholder="مثلاً خانه، محل کار ..."
            className="w-full px-4 py-3 text-base border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition"
            value={name}
            onChange={e => setName(e.target.value)}
          />
        </div>

        {/* Map picker */}
        <div>
          <label className="block text-sm font-semibold text-slate-700 mb-1">موقعیت روی نقشه را انتخاب کنید</label>
          <div className="h-72 rounded-lg overflow-hidden border border-gray-200">
            <LocationPicker
              initialPosition={{ lat: 35.6892, lng: 51.3890 }}
              onLocationSelect={handleMapSelect}
            />
          </div>
          {position && (
            <p className="text-xs text-emerald-600 mt-1 font-medium">
              📍 موقعیت انتخاب شده: {position.lat.toFixed(6)}, {position.lng.toFixed(6)}
            </p>
          )}
        </div>

        {/* Error message */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-700">
            {error}
          </div>
        )}

        {/* Submit button */}
        <button
          onClick={handleSubmit}
          disabled={loading || !name || !position}
          className="w-full py-3 text-base font-bold bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed transition shadow-md"
        >
          {loading ? 'در حال ذخیره...' : '✅ ذخیره آدرس'}
        </button>
      </div>
    </Modal>
  );
};

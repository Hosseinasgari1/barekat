import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';
import type { AvailableBag } from './orderApi';

interface StorePayload {
  name: string;
  description: string;
  address: string;
  latitude: number;
  longitude: number;
  status?: 'PENDING' | 'APPROVED' | 'REJECTED';
}

interface MagicBagPayload {
  id?: number;
  name?: string;
  description?: string;
  category?: string;
  latitude?: number;
  longitude?: number;
  image?: string | File;
  expiry_image?: string | File;
  approval_status?: 'PENDING' | 'APPROVED' | 'REJECTED';
  original_price: string;
  platform_price: string;
  quantity: number;
  pickup_start_time: string;
  pickup_end_time: string;
  is_active?: boolean;
}

interface BagsResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: MagicBagPayload[];
}

export const vendorApi = createApi({
  reducerPath: 'vendorApi',
  baseQuery: fetchBaseQuery({
    baseUrl: import.meta.env.VITE_API_URL || 'http://localhost:8000/api/',
    prepareHeaders: (headers, { endpoint }) => {
      const token = localStorage.getItem('access_token');
      if (token) {
        headers.set('Authorization', `Bearer ${token}`);
      }
      // Skip setting Content-Type for createBag to let browser set the multipart boundary
      if (endpoint !== 'createBag') {
        headers.set('Content-Type', 'application/json');
      }
      return headers;
    },
  }),
  endpoints: (builder) => ({
    getMyStore: builder.query<StorePayload, void>({
      query: () => 'stores/my-store/',
    }),
    updateStore: builder.mutation<StorePayload, StorePayload>({
      query: (body) => ({
        url: 'stores/profile/',
        method: 'POST',
        body,
      }),
    }),
    getBags: builder.query<BagsResponse, void>({
      query: () => 'inventory/bags/',
    }),
    createBag: builder.mutation<MagicBagPayload, FormData | MagicBagPayload>({
      query: (body) => ({
        url: 'inventory/bags/',
        method: 'POST',
        body,
      }),
    }),
    getPendingBags: builder.query<AvailableBag[], void>({
      query: () => 'inventory/admin/pending/',
    }),
    approveRejectBag: builder.mutation<{ detail: string }, { id: number; action: 'approve' | 'reject' }>({
      query: ({ id, action }) => ({
        url: `inventory/admin/bags/${id}/action/`,
        method: 'POST',
        body: { action },
      }),
    }),
  }),
});

export const {
  useGetMyStoreQuery,
  useUpdateStoreMutation,
  useGetBagsQuery,
  useCreateBagMutation,
  useGetPendingBagsQuery,
  useApproveRejectBagMutation,
} = vendorApi;

import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';

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
    prepareHeaders: (headers) => {
      const token = localStorage.getItem('access_token');
      if (token) {
        headers.set('Authorization', `Bearer ${token}`);
      }
      headers.set('Content-Type', 'application/json');
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
    createBag: builder.mutation<MagicBagPayload, MagicBagPayload>({
      query: (body) => ({
        url: 'inventory/bags/',
        method: 'POST',
        body,
      }),
    }),
  }),
});

export const {
  useGetMyStoreQuery,
  useUpdateStoreMutation,
  useGetBagsQuery,
  useCreateBagMutation,
} = vendorApi;

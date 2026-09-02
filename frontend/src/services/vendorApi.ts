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
  tagTypes: ['AdminBags', 'MyBags', 'MyStore'],
  endpoints: (builder) => ({
    getMyStore: builder.query<StorePayload, void>({
      query: () => 'stores/my-store/',
      providesTags: ['MyStore'],
    }),
    updateStore: builder.mutation<StorePayload, StorePayload>({
      query: (body) => ({
        url: 'stores/profile/',
        method: 'POST',
        body,
      }),
      invalidatesTags: ['MyStore'],
    }),
    getBags: builder.query<BagsResponse, void>({
      query: () => 'inventory/bags/',
      providesTags: ['MyBags'],
    }),
    createBag: builder.mutation<MagicBagPayload, FormData | MagicBagPayload>({
      query: (body) => ({
        url: 'inventory/bags/',
        method: 'POST',
        body,
      }),
      invalidatesTags: ['MyBags'],
    }),
    getPendingBags: builder.query<AvailableBag[], void>({
      query: () => 'inventory/admin/pending/',
      providesTags: ['AdminBags'],
    }),
    getAdminBags: builder.query<AvailableBag[], 'PENDING' | 'APPROVED' | 'REJECTED' | 'ALL' | void>({
      query: (status = 'ALL') => {
        const params = status && status !== 'ALL' ? `?status=${status}` : '';
        return `inventory/admin/bags/${params}`;
      },
      providesTags: ['AdminBags'],
    }),
    approveRejectBag: builder.mutation<
      { detail: string; quantity?: number },
      {
        id: number;
        action: 'approve' | 'reject' | 'reopen' | 'activate' | 'deactivate' | 'set_quantity';
        quantity?: number;
      }
    >({
      query: ({ id, action, quantity }) => ({
        url: `inventory/admin/bags/${id}/action/`,
        method: 'POST',
        body: quantity !== undefined ? { action, quantity } : { action },
      }),
      invalidatesTags: ['AdminBags'],
    }),
    searchCatalog: builder.query<any[], string>({
      query: (q) => `inventory/catalog/search/?q=${encodeURIComponent(q)}`,
    }),
    getCatalogSources: builder.query<string[], void>({
      query: () => `inventory/catalog/sources/`,
    }),
    getCatalogCategories: builder.query<string[], string | void>({
      query: (source) => `inventory/catalog/categories/${source ? `?source=${source}` : ''}`,
    }),
    getCatalogProducts: builder.query<{ count: number, results: any[] }, { source?: string, category?: string, page?: number }>({
      query: (params) => {
        let qs = [];
        if (params.source) qs.push(`source=${encodeURIComponent(params.source)}`);
        if (params.category) qs.push(`category=${encodeURIComponent(params.category)}`);
        if (params.page) qs.push(`page=${params.page}`);
        return `inventory/catalog/products/?${qs.join('&')}`;
      }
    }),
  }),
});

export const {
  useGetMyStoreQuery,
  useUpdateStoreMutation,
  useGetBagsQuery,
  useCreateBagMutation,
  useGetPendingBagsQuery,
  useGetAdminBagsQuery,
  useApproveRejectBagMutation,
  useSearchCatalogQuery,
  useGetCatalogSourcesQuery,
  useGetCatalogCategoriesQuery,
  useGetCatalogProductsQuery,
} = vendorApi;

import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';

export interface UserAddress {
  id: number;
  name: string;
  latitude: string;
  longitude: string;
  is_active: boolean;
  created_at: string;
}

interface StoreBrief {
  id: number;
  name: string;
  description: string;
  address: string;
  latitude: number;
  longitude: number;
}

export interface AvailableBag {
  id: number;
  store: StoreBrief | null;
  seller?: number;
  seller_details?: {
    phone_number: string;
    first_name?: string;
    last_name?: string;
  };
  name: string;
  description?: string;
  category: string;
  latitude?: string;
  longitude?: string;
  original_price: string;
  platform_price: string;
  quantity: number;
  pickup_start_time: string;
  pickup_end_time: string;
  distance?: number;
  created_at: string;
}

export interface OrderDetail {
  id: number;
  customer: number;
  customer_details?: {
    phone_number: string;
    first_name?: string;
    last_name?: string;
  };
  magic_bag: number;
  magic_bag_details: {
    id: number;
    store: StoreBrief | null;
    name: string;
    description?: string;
    category: string;
    original_price: string;
    platform_price: string;
    pickup_start_time: string;
    pickup_end_time: string;
  };
  quantity: number;
  total_price: string;
  status: 'PENDING_PAYMENT' | 'PAID' | 'PICKED_UP' | 'CANCELLED';
  pickup_code: string;
  created_at: string;
  updated_at: string;
}

interface CreateOrderRequest {
  magic_bag: number;
  quantity: number;
}

interface VerifyPickupRequest {
  orderId: number;
  pickup_code: string;
}

export const orderApi = createApi({
  reducerPath: 'orderApi',
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
  tagTypes: ['Orders', 'Bags', 'Addresses'],
  endpoints: (builder) => ({
    getAvailableBags: builder.query<AvailableBag[], { latitude?: number; longitude?: number; category?: string } | void>({
      query: (params) => {
        let url = 'inventory/available-bags/';
        const queryParts: string[] = [];
        if (params) {
          if (params.latitude !== undefined && params.longitude !== undefined) {
            queryParts.push(`latitude=${params.latitude}`);
            queryParts.push(`longitude=${params.longitude}`);
          }
          if (params.category) {
            queryParts.push(`category=${params.category}`);
          }
        }
        if (queryParts.length > 0) {
          url += `?${queryParts.join('&')}`;
        }
        return url;
      },
      providesTags: ['Bags'],
    }),
    createOrder: builder.mutation<OrderDetail, CreateOrderRequest>({
      query: (body) => ({
        url: 'orders/',
        method: 'POST',
        body,
      }),
      invalidatesTags: ['Orders', 'Bags'],
    }),
    getMyOrders: builder.query<OrderDetail[], void>({
      query: () => 'orders/my-orders/',
      providesTags: ['Orders'],
    }),
    getVendorOrders: builder.query<OrderDetail[], void>({
      query: () => 'orders/vendor/',
      providesTags: ['Orders'],
    }),
    approveOrder: builder.mutation<OrderDetail, number>({
      query: (id) => ({
        url: `orders/${id}/approve/`,
        method: 'POST',
      }),
      invalidatesTags: ['Orders', 'Bags'],
    }),
    rejectOrder: builder.mutation<OrderDetail, number>({
      query: (id) => ({
        url: `orders/${id}/reject/`,
        method: 'POST',
      }),
      invalidatesTags: ['Orders', 'Bags'],
    }),
    verifyPickup: builder.mutation<OrderDetail, VerifyPickupRequest>({
      query: ({ orderId, pickup_code }) => ({
        url: `orders/${orderId}/verify-pickup/`,
        method: 'POST',
        body: { pickup_code },
      }),
      invalidatesTags: ['Orders'],
    }),
    // ── Address endpoints ──
    getMyAddresses: builder.query<UserAddress[], void>({
      query: () => 'stores/addresses/',
      // DRF global pagination wraps results — extract the array
      transformResponse: (response: UserAddress[] | { results: UserAddress[] }) =>
        Array.isArray(response) ? response : response.results,
      providesTags: ['Addresses'],
    }),
    deleteAddress: builder.mutation<void, number>({
      query: (id) => ({
        url: `stores/addresses/${id}/`,
        method: 'DELETE',
      }),
      invalidatesTags: ['Addresses'],
    }),
    // Sets an address as active server-side (deactivates all others for this user)
    setActiveAddress: builder.mutation<UserAddress, number>({
      query: (id) => ({
        url: `stores/addresses/${id}/set-active/`,
        method: 'POST',
      }),
      invalidatesTags: ['Addresses'],
    }),
  }),
});

export const {
  useGetAvailableBagsQuery,
  useCreateOrderMutation,
  useGetMyOrdersQuery,
  useGetVendorOrdersQuery,
  useApproveOrderMutation,
  useRejectOrderMutation,
  useVerifyPickupMutation,
  useGetMyAddressesQuery,
  useDeleteAddressMutation,
  useSetActiveAddressMutation,
} = orderApi;

export const AvailableBag = {};
export const OrderDetail = {};

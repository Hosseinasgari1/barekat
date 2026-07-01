import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';

interface SendOtpResponse {
  detail: string;
  otp?: string;
}

interface SendOtpRequest {
  phone_number: string;
}

interface UserPayload {
  phone_number: string;
  role: string;
  first_name?: string;
  last_name?: string;
  email?: string;
}

interface VerifyOtpResponse {
  access: string;
  refresh: string;
  user: UserPayload;
}

interface VerifyOtpRequest {
  phone_number: string;
  otp: string;
  role?: string;
}

export const authApi = createApi({
  reducerPath: 'authApi',
  baseQuery: fetchBaseQuery({
    baseUrl: import.meta.env.VITE_API_URL || 'http://localhost:8000/api/',
    prepareHeaders: (headers) => {
      headers.set('Content-Type', 'application/json');
      return headers;
    },
  }),
  endpoints: (builder) => ({
    sendOtp: builder.mutation<SendOtpResponse, SendOtpRequest>({
      query: (body) => ({
        url: 'users/send-otp/',
        method: 'POST',
        body,
      }),
    }),
    verifyOtp: builder.mutation<VerifyOtpResponse, VerifyOtpRequest>({
      query: (body) => ({
        url: 'users/verify-otp/',
        method: 'POST',
        body,
      }),
    }),
  }),
});

export const { useSendOtpMutation, useVerifyOtpMutation } = authApi;

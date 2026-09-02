import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';

export interface AdminUser {
    phone_number: string;
    admin_username: string;
    first_name?: string;
    last_name?: string;
    is_super_admin: boolean;
    admin_permissions: string[];
    is_active: boolean;
    created_at: string;
}

export interface AdminLoginResponse {
    access: string;
    refresh: string;
    user: {
        phone_number: string;
        role: string;
        admin_username: string;
        first_name?: string;
        last_name?: string;
        is_super_admin: boolean;
        admin_permissions: string[];
    };
}

interface AdminLoginRequest {
    username: string;
    password: string;
}

interface CreateAdminRequest {
    admin_username: string;
    password: string;
    first_name?: string;
    last_name?: string;
    admin_permissions: string[];
}

export const adminApi = createApi({
    reducerPath: 'adminApi',
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
    tagTypes: ['Admins'],
    endpoints: (builder) => ({
        adminLogin: builder.mutation<AdminLoginResponse, AdminLoginRequest>({
            query: (body) => ({
                url: 'users/admin/login/',
                method: 'POST',
                body,
            }),
        }),
        getAdmins: builder.query<AdminUser[], void>({
            query: () => 'users/admin/admins/',
            providesTags: ['Admins'],
        }),
        getAdminPermissions: builder.query<{ permissions: string[] }, void>({
            query: () => 'users/admin/permissions/',
        }),
        createAdmin: builder.mutation<AdminUser, CreateAdminRequest>({
            query: (body) => ({
                url: 'users/admin/admins/',
                method: 'POST',
                body,
            }),
            invalidatesTags: ['Admins'],
        }),
        updateAdmin: builder.mutation<AdminUser, { phone_number: string; admin_permissions?: string[]; is_active?: boolean; password?: string }>({
            query: ({ phone_number, ...body }) => ({
                url: `users/admin/admins/${encodeURIComponent(phone_number)}/`,
                method: 'PATCH',
                body,
            }),
            invalidatesTags: ['Admins'],
        }),
        deleteAdmin: builder.mutation<void, string>({
            query: (phone_number) => ({
                url: `users/admin/admins/${encodeURIComponent(phone_number)}/`,
                method: 'DELETE',
            }),
            invalidatesTags: ['Admins'],
        }),
    }),
});

export const {
    useAdminLoginMutation,
    useGetAdminsQuery,
    useGetAdminPermissionsQuery,
    useCreateAdminMutation,
    useUpdateAdminMutation,
    useDeleteAdminMutation,
} = adminApi;

// Human-readable labels for permission keys
export const PERMISSION_LABELS: Record<string, string> = {
    approve_products: 'تایید محصولات',
};

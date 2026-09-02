import React, { useState, useEffect } from 'react';

import {
  BrowserRouter, Routes, Route, Link, useNavigate,
  Navigate, Outlet, useLocation
} from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { setCredentials, setUser, logout } from './features/auth/authSlice';
import { useSendOtpMutation, useVerifyOtpMutation } from './services/authApi';
import {
  useGetMyStoreQuery,
  useUpdateStoreMutation,
  useGetBagsQuery,
  useCreateBagMutation,
  useGetAdminBagsQuery,
  useApproveRejectBagMutation,
  useGetCatalogSourcesQuery,
  useGetCatalogCategoriesQuery,
  useGetCatalogProductsQuery,
} from './services/vendorApi';
import {
  useGetAvailableBagsQuery,
  useCreateOrderMutation,
  useGetMyOrdersQuery,
  useGetVendorOrdersQuery,
  useApproveOrderMutation,
  useRejectOrderMutation,
  useVerifyPickupMutation,
  useSubmitReviewMutation,
  useGetSellerReviewsQuery,
  useGetMyAddressesQuery,
  useDeleteAddressMutation,
  useSetActiveAddressMutation,
} from './services/orderApi';
import type { AvailableBag, UserAddress, OrderDetail, Review } from './services/orderApi';
import {
  useAdminLoginMutation,
  useGetAdminsQuery,
  useGetAdminPermissionsQuery,
  useCreateAdminMutation,
  useUpdateAdminMutation,
  useDeleteAdminMutation,
  PERMISSION_LABELS,
} from './services/adminApi';
import type { AdminUser } from './services/adminApi';
import { ProtectedRoute } from './components/ProtectedRoute';

import type { RootState } from './store';
import api from './services/api';
import { LocationPicker } from './components/LocationPicker';
import { AddressModal } from './components/AddressModal';
import { categories, getCategoryEmoji } from './lib/categories';
import { getMediaUrl } from './lib/format';


// ─────────────────────────────────────────────
// STAR RATING HELPERS
// ─────────────────────────────────────────────
const StarRatingDisplay = ({ rating, size = 'sm' }: { rating: number; size?: 'sm' | 'md' }) => {
  const starSize = size === 'md' ? 'text-lg' : 'text-sm';
  return (
    <span className={`inline-flex items-center gap-0.5 ${starSize}`}>
      {[1, 2, 3, 4, 5].map(star => (
        <span key={star} className={star <= Math.round(rating) ? 'text-amber-400' : 'text-slate-200'}>★</span>
      ))}
    </span>
  );
};

const StarRatingInput = ({ value, onChange }: { value: number; onChange: (v: number) => void }) => (
  <div className="flex items-center justify-center gap-2">
    {[1, 2, 3, 4, 5].map(star => (
      <button
        key={star}
        type="button"
        onClick={() => onChange(star)}
        className={`text-3xl transition-transform hover:scale-110 ${star <= value ? 'text-amber-400' : 'text-slate-200'}`}
      >
        ★
      </button>
    ))}
  </div>
);

const SubmitReviewModal = ({
  order,
  onClose,
}: {
  order: OrderDetail | null;
  onClose: () => void;
}) => {
  const [rating, setRating] = useState(0);
  const [comment, setComment] = useState('');
  const [error, setError] = useState('');
  const [submitReview, { isLoading }] = useSubmitReviewMutation();

  useEffect(() => {
    if (order) {
      setRating(0);
      setComment('');
      setError('');
    }
  }, [order]);

  if (!order) return null;

  const handleSubmit = async () => {
    if (rating < 1) {
      setError('لطفاً امتیاز خود را انتخاب کنید.');
      return;
    }
    setError('');
    try {
      await submitReview({ orderId: order.id, rating, comment }).unwrap();
      onClose();
    } catch (err: any) {
      setError(err.data?.error || 'خطا در ثبت نظر. دوباره تلاش کنید.');
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-black/40 backdrop-blur-sm px-4 pb-4" dir="rtl">
      <div className="w-full max-w-sm bg-white rounded-3xl p-6 shadow-2xl">
        <div className="flex items-center justify-between mb-5">
          <h3 className="text-lg font-black text-slate-800">ثبت امتیاز و نظر</h3>
          <button onClick={onClose} className="w-9 h-9 flex items-center justify-center rounded-full bg-slate-100 text-slate-500 hover:bg-slate-200 transition font-bold">✕</button>
        </div>
        <p className="text-sm text-slate-500 text-center mb-4">
          {order.magic_bag_details?.name} — {order.magic_bag_details?.store?.name ?? 'فروشنده حقیقی'}
        </p>
        <StarRatingInput value={rating} onChange={setRating} />
        <textarea
          value={comment}
          onChange={e => setComment(e.target.value)}
          placeholder="نظر خود را بنویسید (اختیاری)..."
          className="w-full mt-5 p-3 rounded-2xl border border-slate-200 text-sm resize-none h-24 focus:outline-none focus:ring-2 focus:ring-emerald-500/30"
        />
        {error && <p className="mt-3 text-xs font-bold text-red-500 text-center">{error}</p>}
        <button
          onClick={handleSubmit}
          disabled={isLoading}
          className="w-full mt-5 py-3.5 rounded-2xl font-black text-sm bg-gradient-to-r from-emerald-600 to-green-500 text-white shadow-lg shadow-emerald-500/20 hover:brightness-105 active:scale-[0.98] transition disabled:opacity-50"
        >
          {isLoading ? 'در حال ثبت...' : 'ثبت نظر'}
        </button>
      </div>
    </div>
  );
};

const SellerReviewsModal = ({
  bag,
  onClose,
}: {
  bag: AvailableBag | null;
  onClose: () => void;
}) => {
  const storeId = bag?.store?.id;
  const sellerId = bag?.seller;
  const { data, isLoading } = useGetSellerReviewsQuery(
    storeId ? { storeId } : { sellerId: sellerId! },
    { skip: !bag || (!storeId && !sellerId) },
  );

  if (!bag) return null;

  const sellerName = bag.store
    ? bag.store.name
    : bag.seller_details?.first_name || bag.seller_details?.last_name
      ? `${bag.seller_details.first_name || ''} ${bag.seller_details.last_name || ''}`.trim()
      : 'فروشنده حقیقی';

  return (
    <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-black/40 backdrop-blur-sm px-4 pb-4" dir="rtl">
      <div className="w-full max-w-md bg-white rounded-3xl p-6 shadow-2xl max-h-[80vh] flex flex-col">
        <div className="flex items-center justify-between mb-4 flex-shrink-0">
          <div>
            <h3 className="text-lg font-black text-slate-800">نظرات فروشنده</h3>
            <p className="text-xs text-slate-400 mt-0.5">{sellerName}</p>
          </div>
          <button onClick={onClose} className="w-9 h-9 flex items-center justify-center rounded-full bg-slate-100 text-slate-500 hover:bg-slate-200 transition font-bold">✕</button>
        </div>

        {isLoading ? (
          <div className="flex justify-center py-10">
            <div className="w-8 h-8 rounded-full border-4 border-slate-200 border-t-emerald-500 animate-spin" />
          </div>
        ) : (
          <>
            <div className="bg-amber-50 rounded-2xl p-4 text-center mb-4 flex-shrink-0 border border-amber-100">
              {data?.average_rating ? (
                <>
                  <p className="text-3xl font-black text-amber-600">{data.average_rating}</p>
                  <StarRatingDisplay rating={data.average_rating} size="md" />
                  <p className="text-xs text-amber-700/70 mt-1 font-semibold">{data.review_count} نظر</p>
                </>
              ) : (
                <p className="text-sm text-amber-700 font-semibold">هنوز نظری ثبت نشده</p>
              )}
            </div>

            <div className="overflow-y-auto flex-1 space-y-3">
              {data?.reviews && data.reviews.length > 0 ? (
                data.reviews.map((review: Review) => (
                  <div key={review.id} className="bg-slate-50 rounded-2xl p-4 border border-slate-100">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs font-bold text-slate-600">{review.customer.display_name}</span>
                      <StarRatingDisplay rating={review.rating} />
                    </div>
                    {review.comment && (
                      <p className="text-sm text-slate-600 leading-relaxed">{review.comment}</p>
                    )}
                    <p className="text-[10px] text-slate-400 mt-2">
                      {new Date(review.created_at).toLocaleDateString('fa-IR')}
                    </p>
                  </div>
                ))
              ) : (
                <p className="text-center text-sm text-slate-400 py-6">اولین نفری باشید که نظر می‌دهد!</p>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
};


// ─────────────────────────────────────────────
// SINGLE LOGIN PAGE (phone + OTP, no role tabs)
// ─────────────────────────────────────────────
const Login = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const { isAuthenticated } = useSelector((state: RootState) => state.auth);

  const [step, setStep] = useState(1);
  const [phoneNumber, setPhoneNumber] = useState('');
  const [otp, setOtp] = useState('');
  const [mockOtp, setMockOtp] = useState('');
  const [timer, setTimer] = useState(0);
  const [error, setError] = useState('');

  const [sendOtp, { isLoading: isSending }] = useSendOtpMutation();
  const [verifyOtp, { isLoading: isVerifying }] = useVerifyOtpMutation();

  useEffect(() => {
    if (isAuthenticated) navigate('/app/discover', { replace: true });
  }, [isAuthenticated, navigate]);

  useEffect(() => {
    let interval: any = null;
    if (step === 2 && timer > 0) {
      interval = setInterval(() => setTimer(p => p - 1), 1000);
    }
    return () => { if (interval) clearInterval(interval); };
  }, [step, timer]);

  const isPhoneValid = /^(\+98|0)?9\d{9}$/.test(phoneNumber);

  const handleSendCode = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!isPhoneValid) return;
    setError('');
    try {
      const res = await sendOtp({ phone_number: phoneNumber }).unwrap();
      if (res?.otp) setMockOtp(res.otp);
      setTimer(120);
      setStep(2);
    } catch (err: any) {
      setError(err.data?.error || 'خطا در ارسال کد. دوباره تلاش کنید.');
    }
  };

  const handleVerifyCode = async (e: React.FormEvent) => {
    e.preventDefault();
    if (otp.length !== 5) return;
    setError('');
    try {
      // Send role as CUSTOMER always — all users start as customers; shop creation is optional
      const res = await verifyOtp({ phone_number: phoneNumber, otp, role: 'CUSTOMER' }).unwrap();
      dispatch(setCredentials({ accessToken: res.access, refreshToken: res.refresh, user: res.user }));
      navigate('/app/discover', { replace: true });
    } catch (err: any) {
      setError(err.data?.error || 'کد نامعتبر یا منقضی شده است.');
    }
  };

  const fmt = (s: number) =>
    `${Math.floor(s / 60).toString().padStart(2, '0')}:${(s % 60).toString().padStart(2, '0')}`;

  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-4 bg-gradient-to-b from-amber-50 via-white to-emerald-50" dir="rtl">
      {/* Warm decorative elements */}
      <div className="absolute top-0 right-0 w-64 h-64 bg-amber-200/20 rounded-full blur-[80px] pointer-events-none" />
      <div className="absolute bottom-0 left-0 w-80 h-80 bg-emerald-200/15 rounded-full blur-[100px] pointer-events-none" />
      <div className="absolute top-1/3 left-1/4 w-40 h-40 bg-amber-100/30 rounded-full blur-[60px] pointer-events-none" />

      <div className="w-full max-w-sm z-10 page-enter">
        {/* Illustration - Old man with bag */}
        <div className="flex justify-center mb-4 animate-float">
          <img
            src="/old-man.svg"
            alt="پدربزرگ مهربان با کیسه برکت"
            className="w-48 h-auto drop-shadow-lg"
          />
        </div>

        {/* Brand name */}
        <div className="text-center mb-6">
          <h1 className="text-4xl font-black text-emerald-800 mb-2">برکت</h1>
          <p className="text-amber-700 text-sm font-semibold">غذای اضافی، قیمت مناسب، سفره پربرکت</p>
          <div className="flex items-center justify-center gap-2 mt-2">
            <span className="text-xs text-emerald-600 bg-emerald-50 px-3 py-1 rounded-full border border-emerald-100">
              🌱 کاهش پسماند غذا
            </span>
            <span className="text-xs text-amber-600 bg-amber-50 px-3 py-1 rounded-full border border-amber-100">
              ❤️ اشتراک‌گذاری
            </span>
          </div>
        </div>

        {/* Login card */}
        <div className="bg-white rounded-3xl shadow-xl shadow-amber-100/40 p-6 border border-amber-100/50">
          {step === 1 ? (
            <form onSubmit={handleSendCode} className="space-y-5">
              <div className="text-center">
                <h2 className="text-xl font-black text-slate-800 mb-1">به برکت خوش آمدید! 👋</h2>
                <p className="text-slate-500 text-xs">برای شروع، شماره موبایل خود را وارد کنید</p>
              </div>
              {error && (
                <div className="p-3 rounded-xl bg-red-50 border border-red-200 text-red-600 text-sm font-medium text-center">
                  {error}
                </div>
              )}
              <div className="relative">
                <input
                  type="text"
                  required
                  placeholder="09123456789"
                  value={phoneNumber}
                  onChange={e => setPhoneNumber(e.target.value)}
                  className="w-full px-4 py-4 rounded-2xl bg-amber-50/50 border-2 border-amber-200 text-slate-800 text-center tracking-widest text-xl font-bold focus:outline-none focus:border-emerald-500 focus:bg-white transition-all placeholder:text-amber-300"
                />
                <span className="absolute left-4 top-1/2 -translate-y-1/2 text-2xl">📱</span>
              </div>
              <button
                type="submit"
                disabled={isSending || !isPhoneValid}
                className="w-full py-4 rounded-2xl font-black text-base bg-gradient-to-r from-emerald-600 to-emerald-500 text-white shadow-lg shadow-emerald-500/30 hover:shadow-emerald-500/40 hover:brightness-105 active:scale-[0.98] transition-all disabled:opacity-50 disabled:shadow-none"
              >
                {isSending ? (
                  <span className="flex items-center justify-center gap-2">
                    <span className="animate-spin">⏳</span> در حال ارسال...
                  </span>
                ) : (
                  'دریافت کد تایید ✨'
                )}
              </button>
            </form>
          ) : (
            <form onSubmit={handleVerifyCode} className="space-y-5">
              <div className="text-center">
                <h2 className="text-xl font-black text-slate-800 mb-1">کد تایید را وارد کنید</h2>
                <p className="text-slate-500 text-xs">کد ۵ رقمی ارسال شده به <span className="font-bold text-emerald-600">{phoneNumber}</span></p>
              </div>
              {error && (
                <div className="p-3 rounded-xl bg-red-50 border border-red-200 text-red-600 text-sm font-medium text-center">
                  {error}
                </div>
              )}
              {mockOtp && (
                <div className="p-4 rounded-2xl bg-emerald-50 border-2 border-emerald-200 text-center animate-bounce-in">
                  <p className="text-xs text-emerald-600 font-semibold mb-2">کد تستی شما:</p>
                  <span className="text-3xl font-black tracking-[0.5em] text-emerald-700 select-all">{mockOtp}</span>
                </div>
              )}
              <div className="relative">
                <input
                  type="text"
                  maxLength={5}
                  required
                  placeholder="• • • • •"
                  value={otp}
                  onChange={e => setOtp(e.target.value.replace(/\D/g, ''))}
                  className="w-full px-4 py-4 rounded-2xl bg-amber-50/50 border-2 border-amber-200 text-center tracking-[1.2em] text-2xl font-black focus:outline-none focus:border-emerald-500 focus:bg-white transition-all"
                />
              </div>
              <div className="flex items-center justify-between text-sm px-1">
                {timer > 0
                  ? <span className="text-slate-500 font-semibold flex items-center gap-1">⏱ {fmt(timer)}</span>
                  : <span className="text-red-500 font-semibold text-xs">⏰ کد منقضی شد</span>}
                <button type="button" disabled={timer > 0 || isSending} onClick={() => handleSendCode()}
                  className="text-emerald-600 font-bold text-sm disabled:text-slate-300 disabled:cursor-not-allowed hover:text-emerald-700 transition">
                  ارسال مجدد 🔄
                </button>
              </div>
              <div className="flex gap-3">
                <button
                  type="submit"
                  disabled={isVerifying || otp.length !== 5}
                  className="flex-1 py-4 rounded-2xl font-black bg-gradient-to-r from-emerald-600 to-emerald-500 text-white shadow-lg shadow-emerald-500/30 hover:shadow-emerald-500/40 hover:brightness-105 active:scale-[0.98] transition-all disabled:opacity-50"
                >
                  {isVerifying ? (
                    <span className="flex items-center justify-center gap-2">
                      <span className="animate-spin">⏳</span> بررسی...
                    </span>
                  ) : (
                    'ورود به برکت ✅'
                  )}
                </button>
                <button type="button" onClick={() => { setStep(1); setError(''); }}
                  className="px-5 py-4 rounded-2xl font-bold border-2 border-amber-200 text-slate-600 hover:bg-amber-50 hover:border-amber-300 transition-all">
                  بازگشت
                </button>
              </div>
            </form>
          )}
        </div>

        {/* Footer */}
        <p className="text-center text-xs text-slate-400 mt-6">
          با ورود، <span className="text-emerald-600">شرایط استفاده</span> و <span className="text-emerald-600">حریم خصوصی</span> را می‌پذیرید
        </p>
      </div>
    </div>
  );
};

// ─────────────────────────────────────────────
// UNIFIED APP LAYOUT (Snapp-style bottom nav)
// ─────────────────────────────────────────────
const AppLayout = () => {
  const { pathname } = useLocation();
  const dispatch = useDispatch();
  const { userInfo } = useSelector((state: RootState) => state.auth);

  useEffect(() => {
    if (userInfo) {
      api.get('users/profile/')
        .then(r => {
          dispatch(setUser(r.data));
        })
        .catch(() => { });
    }
  }, [dispatch]);

  const tabs = [
    { path: '/app/discover', icon: '🏠', label: 'خانه', activeIcon: '🏡' },
    { path: '/app/orders', icon: '📋', label: 'سفارشها', activeIcon: '📦' },

    { path: '/app/shop', icon: '🏪', label: 'فروشگاه', activeIcon: '🛍️' },
    { path: '/app/profile', icon: '👤', label: 'پروفایل', activeIcon: '👨‍💼' },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-b from-amber-50/30 to-emerald-50/20 flex flex-col" dir="rtl">
      {/* Top bar - Warm friendly header */}
      <header className="bg-white/90 backdrop-blur-md border-b border-amber-100/50 sticky top-0 z-40 shadow-sm">
        <div className="max-w-lg mx-auto px-4 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-500 to-emerald-600 flex items-center justify-center shadow-md shadow-emerald-500/20">
              <span className="text-white font-black text-lg">ب</span>
            </div>
            <div>
              <span className="font-black text-emerald-800 text-lg block leading-tight">برکت</span>
              <span className="text-[10px] text-amber-600 font-semibold">🌱 سفره پربرکت</span>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 bg-amber-50 px-3 py-1.5 rounded-full border border-amber-100">
              <span className="text-lg">👋</span>
              <span className="text-xs text-amber-800 font-bold">
                {userInfo?.first_name || 'دوست عزیز'}
              </span>
            </div>
            <button
              onClick={() => dispatch(logout())}
              className="w-9 h-9 flex items-center justify-center rounded-full bg-red-50 text-red-500 hover:bg-red-100 transition-all hover:scale-105 active:scale-95"
              title="خروج از حساب"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
                <polyline points="16 17 21 12 16 7" />
                <line x1="21" y1="12" x2="9" y2="12" />
              </svg>
            </button>
          </div>
        </div>
      </header>

      {/* Page content */}
      <main className="flex-grow max-w-lg mx-auto w-full px-4 py-5 pb-28 page-enter">
        <Outlet />
      </main>

      {/* Bottom navigation - Warm friendly style */}
      <nav className="fixed bottom-0 left-0 right-0 z-50 bg-white/95 backdrop-blur-md border-t border-amber-100/50 shadow-lg shadow-amber-100/20">
        <div className="max-w-lg mx-auto px-2 h-18 flex items-center justify-around">
          {tabs.map(t => {
            const isActive = pathname === t.path;
            return (
              <Link
                key={t.path}
                to={t.path}
                className={`flex flex-col items-center justify-center w-16 py-2 rounded-2xl transition-all duration-300 ${isActive
                  ? 'text-emerald-700 bg-emerald-50 scale-105 shadow-sm'
                  : 'text-slate-400 hover:text-slate-600 hover:bg-amber-50/50'
                  }`}
              >
                <span className={`text-xl transition-transform duration-300 ${isActive ? 'scale-110' : ''}`}>
                  {isActive ? t.activeIcon : t.icon}
                </span>
                <span className={`text-[10px] mt-1 transition-all ${isActive ? 'font-black' : 'font-bold'}`}>
                  {t.label}
                </span>
                {isActive && (
                  <div className="w-1 h-1 rounded-full bg-emerald-500 mt-1" />
                )}
              </Link>
            );
          })}
        </div>
      </nav>
    </div>
  );
};
const DiscoveryPage = () => {
  const [isAddressModalOpen, setIsAddressModalOpen] = useState(false);
  const [selectedBag, setSelectedBag] = useState<AvailableBag | null>(null);
  const [reviewsBag, setReviewsBag] = useState<AvailableBag | null>(null);
  const [addressDropdownOpen, setAddressDropdownOpen] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [sortMode, setSortMode] = useState<'distance' | 'rating'>('distance');

  const { data: addresses, refetch: refetchAddresses } = useGetMyAddressesQuery();
  const [deleteAddress] = useDeleteAddressMutation();
  const [setActiveAddressOnServer] = useSetActiveAddressMutation();

  const activeAddress = addresses?.find(a => a.is_active) ?? null;

  const { data: bags, isLoading: bagsLoading, refetch: refetchBags } = useGetAvailableBagsQuery(
    activeAddress
      ? {
        latitude: parseFloat(activeAddress.latitude),
        longitude: parseFloat(activeAddress.longitude),
        category: selectedCategory ?? undefined,
        sort: sortMode,
      }
      : undefined
  );

  useEffect(() => { refetchBags(); }, [activeAddress?.id, selectedCategory, sortMode, refetchBags]);

  const handleSelectAddress = async (addr: UserAddress) => {
    if (addr.is_active) { setAddressDropdownOpen(false); return; }
    await setActiveAddressOnServer(addr.id);
    setAddressDropdownOpen(false);
  };

  const bagsList = bags || [];

  const discoverCategories = [
    { value: null, label: '🍲 همه' },
    ...categories
  ];

  return (
    <div className="space-y-5">
      {/* ── Hero / address section ── */}
      <div className="bg-gradient-to-br from-emerald-600 via-emerald-500 to-green-500 rounded-3xl p-5 text-white shadow-xl shadow-emerald-500/20">
        <div className="flex items-center justify-between mb-3">
          <div>
            <p className="text-emerald-100 text-xs font-semibold">موقعیت شما</p>
            <h2 className="text-lg font-black mt-0.5">
              {activeAddress ? activeAddress.name : '📍 آدرسی انتخاب نشده'}
            </h2>
          </div>
          <button
            onClick={() => setIsAddressModalOpen(true)}
            className="flex items-center gap-1.5 bg-white/20 hover:bg-white/30 text-white text-xs font-bold px-4 py-2 rounded-xl transition backdrop-blur-sm"
          >
            <span className="text-base">＋</span> آدرس جدید
          </button>
        </div>

        {/* Address dropdown */}
        <div className="relative mt-3">
          <button
            onClick={() => setAddressDropdownOpen(v => !v)}
            className="w-full flex items-center justify-between bg-white/15 hover:bg-white/25 backdrop-blur-sm rounded-2xl px-4 py-3 transition"
          >
            <div className="flex items-center gap-2.5">
              <span className="text-base">{activeAddress ? '📍' : '🗺️'}</span>
              <div className="text-right">
                <p className="text-[10px] text-emerald-100 font-semibold">موقعیت فعال</p>
                <p className="text-sm font-black text-white mt-0.5">
                  {activeAddress ? activeAddress.name : 'آدرسی انتخاب نشده'}
                </p>
              </div>
            </div>
            <span className="text-white/70 text-lg">{addressDropdownOpen ? '▲' : '▼'}</span>
          </button>

          {addressDropdownOpen && (
            <div className="absolute top-full right-0 left-0 mt-2 bg-white rounded-2xl shadow-2xl shadow-slate-900/20 border border-slate-100 overflow-hidden z-50">
              {addresses && addresses.length > 0 ? (
                <>
                  <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wide px-4 pt-3 pb-1">آدرس‌های ذخیره‌شده</p>
                  {addresses.map(addr => (
                    <div key={addr.id} className={`flex items-center justify-between px-4 py-3 border-b border-slate-50 last:border-0 transition ${addr.is_active ? 'bg-emerald-50' : 'hover:bg-slate-50 cursor-pointer'
                      }`}
                      onClick={() => handleSelectAddress(addr)}
                    >
                      <div className="flex items-center gap-2.5">
                        <span className="text-base">{addr.is_active ? '📍' : '🏠'}</span>
                        <div>
                          <p className={`text-sm font-black ${addr.is_active ? 'text-emerald-700' : 'text-slate-700'}`}>{addr.name}</p>
                          <p className="text-[10px] text-slate-400 font-mono">{parseFloat(addr.latitude).toFixed(4)}, {parseFloat(addr.longitude).toFixed(4)}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        {addr.is_active && <span className="text-[10px] font-black text-emerald-600 bg-emerald-100 px-2 py-0.5 rounded-full">فعال</span>}
                        <button
                          onClick={e => { e.stopPropagation(); deleteAddress(addr.id); refetchAddresses(); }}
                          className="w-6 h-6 flex items-center justify-center rounded-full bg-red-50 text-red-400 hover:bg-red-100 text-xs transition"
                          title="حذف"
                        >✕</button>
                      </div>
                    </div>
                  ))}
                </>
              ) : (
                <p className="text-xs text-slate-400 text-center p-4">هیچ آدرسی ذخیره نشده</p>
              )}
              <div className="p-3 border-t border-slate-100">
                <button
                  onClick={() => { setAddressDropdownOpen(false); setIsAddressModalOpen(true); }}
                  className="w-full py-2.5 rounded-xl text-xs font-black text-emerald-700 bg-emerald-50 hover:bg-emerald-100 transition border border-emerald-100"
                >
                  ＋ افزودن آدرس جدید
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Address modal */}
      <AddressModal
        isOpen={isAddressModalOpen}
        onClose={() => setIsAddressModalOpen(false)}
        onCreated={() => { refetchAddresses(); setIsAddressModalOpen(false); }}
      />

      {/* ── Category Selector Bar ── */}
      <div className="flex gap-2 overflow-x-auto pb-1 scrollbar-none" style={{ scrollbarWidth: 'none' }}>
        {discoverCategories.map(c => {
          const isActive = selectedCategory === c.value;
          return (
            <button
              key={c.value ?? 'all'}
              onClick={() => setSelectedCategory(c.value)}
              className={`whitespace-nowrap px-4 py-2.5 rounded-2xl text-xs font-black transition-all duration-200 ${isActive
                ? 'bg-emerald-600 text-white shadow-md shadow-emerald-500/20'
                : 'bg-white text-slate-600 border border-slate-100 hover:bg-slate-50'
                }`}
            >
              {c.label}
            </button>
          );
        })}
      </div>

      {/* ── Sort toggle ── */}
      {activeAddress && (
        <div className="flex gap-2">
          <button
            onClick={() => setSortMode('distance')}
            className={`flex-1 py-2.5 rounded-2xl text-xs font-black transition-all ${sortMode === 'distance'
              ? 'bg-emerald-600 text-white shadow-md shadow-emerald-500/20'
              : 'bg-white text-slate-600 border border-slate-100 hover:bg-slate-50'
              }`}
          >
            📍 نزدیک‌ترین
          </button>
          <button
            onClick={() => setSortMode('rating')}
            className={`flex-1 py-2.5 rounded-2xl text-xs font-black transition-all ${sortMode === 'rating'
              ? 'bg-amber-500 text-white shadow-md shadow-amber-500/20'
              : 'bg-white text-slate-600 border border-slate-100 hover:bg-slate-50'
              }`}
          >
            ⭐ بالاترین امتیاز
          </button>
        </div>
      )}

      {/* ── Bags section ── */}
      <div className="space-y-4">
        {!activeAddress ? (
          <div className="bg-white rounded-3xl p-8 text-center shadow-sm border border-slate-100">
            <span className="text-5xl block mb-3">📍</span>
            <h3 className="font-black text-slate-700 text-base mb-1">لطفاً موقعیت خود را انتخاب کنید</h3>
            <p className="text-xs text-slate-400 mb-4">برای مشاهده نزدیک‌ترین کیسه‌های غذا و محصولات اطراف خود، آدرس فعال انتخاب کنید</p>
            <button
              onClick={() => setIsAddressModalOpen(true)}
              className="px-6 py-3 rounded-2xl font-black text-sm bg-emerald-600 text-white shadow-lg shadow-emerald-500/20 hover:brightness-105 active:scale-[0.98] transition"
            >
              ＋ افزودن آدرس جدید
            </button>
          </div>
        ) : bagsLoading ? (
          <div className="flex flex-col items-center justify-center h-40 gap-3">
            <div className="w-10 h-10 rounded-full border-4 border-slate-200 border-t-emerald-500 animate-spin" />
            <span className="text-sm text-slate-500 font-semibold">در حال جستجو...</span>
          </div>
        ) : bagsList.length === 0 ? (
          <div className="bg-white rounded-3xl p-10 text-center shadow-sm border border-slate-100">
            <span className="text-5xl block mb-3">🌾</span>
            <h3 className="font-black text-slate-700 text-base mb-1">محصولی یافت نشد</h3>
            <p className="text-xs text-slate-400">
              در ۱۰ کیلومتری {activeAddress.name} محصولی {selectedCategory ? 'در این دسته‌بندی ' : ''}وجود ندارد
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {bagsList.map(bag => (
              <div
                key={bag.id}
                onClick={() => setSelectedBag(bag)}
                className="bg-white rounded-3xl p-5 shadow-sm border border-slate-100 hover:shadow-md hover:border-emerald-100 cursor-pointer transition-all active:scale-[0.99] group"
              >
                {/* Product/Store header */}
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <div className="w-12 h-12 rounded-2xl overflow-hidden border border-slate-100 bg-slate-50 flex items-center justify-center text-2xl shadow-sm flex-shrink-0">
                      {bag.image ? (
                        <img src={getMediaUrl(bag.image as string)} alt="Product" className="w-full h-full object-cover" />
                      ) : (
                        getCategoryEmoji(bag.category)
                      )}
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <h3 className="font-black text-slate-800 text-sm group-hover:text-emerald-700 transition-colors">
                          {bag.name}
                        </h3>
                        <span className="text-[9px] bg-slate-100 text-slate-500 font-bold px-1.5 py-0.5 rounded-md">
                          {categories.find(c => c.value === bag.category)?.label.split(' ').slice(1).join(' ') || bag.category}
                        </span>
                      </div>
                      <p className="text-xs text-slate-400 mt-0.5 font-semibold">
                        {bag.store
                          ? `🏪 ${bag.store.name} (${bag.store.address})`
                          : `👤 فروشنده حقیقی: ${bag.seller_details?.first_name || bag.seller_details?.last_name
                            ? `${bag.seller_details.first_name || ''} ${bag.seller_details.last_name || ''}`.trim()
                            : 'کاربر برکت'}`}
                      </p>
                      {bag.seller_rating != null && bag.seller_rating_count != null && bag.seller_rating_count > 0 && (
                        <button
                          onClick={e => { e.stopPropagation(); setReviewsBag(bag); }}
                          className="flex items-center gap-1 mt-1 text-xs font-bold text-amber-600 hover:text-amber-700 transition"
                        >
                          <span className="text-amber-400">★</span>
                          <span>{bag.seller_rating}</span>
                          <span className="text-slate-400 font-semibold">({bag.seller_rating_count})</span>
                        </button>
                      )}
                    </div>
                  </div>
                  {bag.distance !== undefined && (
                    <span className="text-xs font-black text-emerald-600 bg-emerald-50 border border-emerald-100 px-2.5 py-1 rounded-full flex-shrink-0">
                      📍 {bag.distance} km
                    </span>
                  )}
                </div>

                <div className="h-px bg-slate-50 my-3" />

                {/* Info row */}
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-[10px] text-slate-400 font-semibold">بازه تحویل</p>
                    <p className="text-xs font-black text-slate-700 mt-0.5" dir="ltr">
                      ⏱ {bag.pickup_start_time.slice(0, 5)} – {bag.pickup_end_time.slice(0, 5)}
                    </p>
                  </div>
                  <div className="text-center">
                    <p className="text-[10px] text-slate-400 font-semibold">موجودی</p>
                    <p className="text-xs font-black text-amber-600 mt-0.5">📦 {bag.quantity} عدد</p>
                  </div>
                  <div className="text-left">
                    <p className="text-[10px] text-slate-400 line-through">{parseFloat(bag.original_price).toLocaleString()} ﷼</p>
                    <p className="text-base font-black text-emerald-600">{parseFloat(bag.platform_price).toLocaleString()} ﷼</p>
                  </div>
                </div>

                <div className="mt-3 w-full py-2.5 rounded-xl text-center text-xs font-black bg-gradient-to-r from-emerald-600 to-green-500 text-white shadow-md shadow-emerald-500/20 group-hover:brightness-105 transition">
                  🛒 دریافت کیسه جادویی
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <CheckoutModal bag={selectedBag} onClose={() => setSelectedBag(null)} />
      <SellerReviewsModal bag={reviewsBag} onClose={() => setReviewsBag(null)} />
    </div>
  );
};

// Checkout invoice modal — sends buyer to the (fake) payment gateway
const CheckoutModal = ({ bag, onClose }: { bag: AvailableBag | null; onClose: () => void }) => {
  const navigate = useNavigate();
  const [qty, setQty] = useState(1);
  const [errorMsg, setErrorMsg] = useState('');

  useEffect(() => { setQty(1); setErrorMsg(''); }, [bag]);
  if (!bag) return null;

  const total = parseFloat(bag.platform_price) * qty;
  const isCreating = false;

  const handleCheckout = () => {
    setErrorMsg('');
    onClose();
    // Hand off to the mock payment gateway; order is created after "payment".
    navigate('/app/payment', { state: { bag, qty } });
  };


  return (
    <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-black/40 backdrop-blur-sm px-4 pb-4" dir="rtl">
      <div className="w-full max-w-sm bg-white rounded-3xl p-6 shadow-2xl">
        <div className="flex items-center justify-between mb-5">
          <h3 className="text-xl font-black text-slate-800">خرید کیسه جادویی</h3>
          <button onClick={onClose} className="w-9 h-9 flex items-center justify-center rounded-full bg-slate-100 text-slate-500 hover:bg-slate-200 transition font-bold">✕</button>
        </div>

        <div className="bg-emerald-50 rounded-2xl p-4 mb-5 flex items-center gap-3">
          <div className="w-12 h-12 rounded-xl bg-emerald-100 flex items-center justify-center text-2xl">
            {getCategoryEmoji(bag.category)}
          </div>
          <div>
            <p className="font-black text-slate-800 text-sm">{bag.name}</p>
            <p className="text-xs text-slate-500 font-bold mt-0.5">
              {bag.store ? `🏪 ${bag.store.name}` : '👤 فروشنده حقیقی'}
            </p>
            <p className="text-xs text-emerald-600 font-semibold mt-0.5" dir="ltr">
              ⏱ {bag.pickup_start_time.slice(0, 5)} – {bag.pickup_end_time.slice(0, 5)}
            </p>
          </div>
        </div>

        {errorMsg && <div className="mb-4 p-3 rounded-xl bg-red-50 border border-red-200 text-red-600 text-xs font-bold">{errorMsg}</div>}

        <div className="flex items-center justify-between mb-5 bg-slate-50 rounded-2xl p-4">
          <span className="text-sm font-bold text-slate-700">تعداد</span>
          <div className="flex items-center gap-3">
            <button onClick={() => setQty(q => Math.max(1, q - 1))} className="w-9 h-9 rounded-xl bg-white border border-slate-200 font-black text-slate-600 hover:bg-slate-100 transition">−</button>
            <span className="w-8 text-center font-black text-slate-800">{qty}</span>
            <button onClick={() => setQty(q => Math.min(bag.quantity, q + 1))} className="w-9 h-9 rounded-xl bg-white border border-slate-200 font-black text-slate-600 hover:bg-slate-100 transition">+</button>
          </div>
        </div>

        <div className="flex items-center justify-between mb-5 px-1">
          <span className="text-sm text-slate-500 font-semibold">مجموع پرداختی:</span>
          <span className="text-xl font-black text-emerald-600">{total.toLocaleString()} ﷼</span>
        </div>

        <button
          onClick={handleCheckout}
          disabled={isCreating}
          className="w-full py-4 rounded-2xl font-black text-base bg-gradient-to-r from-emerald-600 to-green-500 text-white shadow-lg shadow-emerald-500/30 hover:brightness-105 active:scale-[0.98] transition-all disabled:opacity-50"
        >
          💳 ادامه و پرداخت
        </button>

      </div>
    </div>
  );
};

// ─────────────────────────────────────────────
// FAKE PAYMENT GATEWAY (mock — no real money)
// ─────────────────────────────────────────────
const PaymentPage = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const state = (location.state || {}) as { bag?: AvailableBag; qty?: number };
  const bag = state.bag;
  const qty = state.qty ?? 1;

  const [createOrder] = useCreateOrderMutation();

  const [cardNumber, setCardNumber] = useState('');
  const [expiry, setExpiry] = useState('');
  const [cvv, setCvv] = useState('');
  const [pin, setPin] = useState('');
  const [phase, setPhase] = useState<'form' | 'processing' | 'success' | 'failed'>('form');
  const [errorMsg, setErrorMsg] = useState('');
  const [secondsLeft, setSecondsLeft] = useState(600); // 10-minute mock gateway timer

  // If the page is opened directly without a selected bag, bounce back home.
  useEffect(() => {
    if (!bag) navigate('/app/discover', { replace: true });
  }, [bag, navigate]);

  // Gateway countdown
  useEffect(() => {
    if (phase !== 'form') return;
    if (secondsLeft <= 0) return;
    const t = setInterval(() => setSecondsLeft(s => s - 1), 1000);
    return () => clearInterval(t);
  }, [phase, secondsLeft]);

  if (!bag) return null;

  const total = parseFloat(bag.platform_price) * qty;

  // Formatting helpers for the card inputs
  const formatCard = (v: string) =>
    v.replace(/\D/g, '').slice(0, 16).replace(/(.{4})/g, '$1 ').trim();
  const formatExpiry = (v: string) => {
    const digits = v.replace(/\D/g, '').slice(0, 4);
    return digits.length > 2 ? `${digits.slice(0, 2)}/${digits.slice(2)}` : digits;
  };

  const cardDigits = cardNumber.replace(/\s/g, '');
  const isValid =
    cardDigits.length === 16 &&
    /^\d{2}\/\d{2}$/.test(expiry) &&
    cvv.length >= 3 && cvv.length <= 4 &&
    pin.length >= 4;

  const fmtTime = (s: number) =>
    `${Math.floor(s / 60).toString().padStart(2, '0')}:${(s % 60).toString().padStart(2, '0')}`;

  const handlePay = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!isValid) return;
    setErrorMsg('');
    setPhase('processing');
    // Simulate a payment-gateway round-trip.
    await new Promise(res => setTimeout(res, 2200));
    try {
      await createOrder({ magic_bag: bag.id, quantity: qty }).unwrap();
      setPhase('success');
      // Auto-redirect to the buyer's orders after a short confirmation.
      setTimeout(() => navigate('/app/orders', { replace: true }), 1800);
    } catch (err: any) {
      setErrorMsg(err.data?.error || 'خطا در ثبت سفارش پس از پرداخت.');
      setPhase('failed');
    }
  };

  return (
    <div className="min-h-[70vh] flex flex-col items-center justify-center" dir="rtl">
      <div className="w-full max-w-sm">
        {/* Gateway header (mimics a bank PSP page) */}
        <div className="bg-gradient-to-l from-indigo-600 to-blue-600 rounded-t-3xl p-4 text-white shadow-lg">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-2xl">🏦</span>
              <div>
                <p className="font-black text-sm leading-tight">درگاه پرداخت برکت‌پی</p>
                <p className="text-[10px] text-blue-100">پرداخت آزمایشی (شبیه‌سازی)</p>
              </div>
            </div>
            {phase === 'form' && (
              <span className="text-xs font-black bg-white/20 px-2.5 py-1 rounded-lg" dir="ltr">⏱ {fmtTime(secondsLeft)}</span>
            )}
          </div>
        </div>

        <div className="bg-white rounded-b-3xl shadow-xl border border-slate-100 border-t-0 p-6">
          {/* Amount summary */}
          <div className="bg-slate-50 rounded-2xl p-4 mb-5 flex items-center justify-between border border-slate-100">
            <div className="flex items-center gap-2">
              <span className="text-xl">{getCategoryEmoji(bag.category)}</span>
              <div>
                <p className="text-xs font-black text-slate-700">{bag.name}</p>
                <p className="text-[10px] text-slate-400">{bag.store ? bag.store.name : 'فروشنده حقیقی'} • {qty} عدد</p>
              </div>
            </div>
            <div className="text-left">
              <p className="text-[10px] text-slate-400">مبلغ قابل پرداخت</p>
              <p className="text-base font-black text-indigo-600">{total.toLocaleString()} ﷼</p>
            </div>
          </div>

          {phase === 'success' ? (
            <div className="text-center py-6">
              <div className="w-16 h-16 mx-auto rounded-full bg-emerald-100 flex items-center justify-center text-4xl mb-3 animate-bounce-in">✅</div>
              <h3 className="font-black text-emerald-700 text-lg">پرداخت موفق بود!</h3>
              <p className="text-xs text-slate-400 mt-1">در حال انتقال به سفارش‌های شما...</p>
            </div>
          ) : phase === 'processing' ? (
            <div className="text-center py-8">
              <div className="w-12 h-12 mx-auto rounded-full border-4 border-slate-200 border-t-indigo-500 animate-spin mb-4" />
              <p className="text-sm font-black text-slate-600">در حال پردازش پرداخت...</p>
              <p className="text-xs text-slate-400 mt-1">لطفاً صفحه را نبندید</p>
            </div>
          ) : (
            <form onSubmit={handlePay} className="space-y-4">
              {(errorMsg || phase === 'failed') && (
                <div className="p-3 rounded-xl bg-red-50 border border-red-200 text-red-600 text-xs font-bold text-center">
                  {errorMsg || 'پرداخت ناموفق بود. دوباره تلاش کنید.'}
                </div>
              )}
              <div>
                <label className="block text-xs font-bold text-slate-500 mb-1.5">شماره کارت</label>
                <input
                  type="text"
                  inputMode="numeric"
                  required
                  dir="ltr"
                  value={cardNumber}
                  onChange={e => setCardNumber(formatCard(e.target.value))}
                  placeholder="6037 9911 2233 4455"
                  className="w-full px-4 py-3 rounded-xl bg-slate-50 border border-slate-200 focus:outline-none focus:border-indigo-500 focus:bg-white text-center tracking-widest font-black text-slate-700 transition"
                />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-bold text-slate-500 mb-1.5">تاریخ انقضا</label>
                  <input
                    type="text"
                    inputMode="numeric"
                    required
                    dir="ltr"
                    value={expiry}
                    onChange={e => setExpiry(formatExpiry(e.target.value))}
                    placeholder="MM/YY"
                    className="w-full px-3 py-3 rounded-xl bg-slate-50 border border-slate-200 focus:outline-none focus:border-indigo-500 text-center font-black text-slate-700 transition"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-500 mb-1.5">CVV2</label>
                  <input
                    type="text"
                    inputMode="numeric"
                    required
                    dir="ltr"
                    value={cvv}
                    onChange={e => setCvv(e.target.value.replace(/\D/g, '').slice(0, 4))}
                    placeholder="***"
                    className="w-full px-3 py-3 rounded-xl bg-slate-50 border border-slate-200 focus:outline-none focus:border-indigo-500 text-center font-black text-slate-700 transition"
                  />
                </div>
              </div>
              <div>
                <label className="block text-xs font-bold text-slate-500 mb-1.5">رمز دوم (رمز پویا)</label>
                <input
                  type="password"
                  inputMode="numeric"
                  required
                  dir="ltr"
                  value={pin}
                  onChange={e => setPin(e.target.value.replace(/\D/g, '').slice(0, 8))}
                  placeholder="••••••"
                  className="w-full px-4 py-3 rounded-xl bg-slate-50 border border-slate-200 focus:outline-none focus:border-indigo-500 focus:bg-white text-center tracking-[0.4em] font-black text-slate-700 transition"
                />
              </div>

              <button
                type="submit"
                disabled={!isValid || secondsLeft <= 0}
                className="w-full py-4 rounded-2xl font-black text-base bg-gradient-to-l from-indigo-600 to-blue-600 text-white shadow-lg shadow-indigo-500/30 hover:brightness-105 active:scale-[0.98] transition-all disabled:opacity-50"
              >
                💳 پرداخت {total.toLocaleString()} ﷼
              </button>
              <button
                type="button"
                onClick={() => navigate('/app/discover')}
                className="w-full py-3 rounded-2xl font-bold text-slate-500 hover:bg-slate-50 transition text-sm"
              >
                انصراف و بازگشت
              </button>
              <p className="text-center text-[10px] text-slate-400 pt-1">
                🔒 این یک درگاه آزمایشی است؛ هیچ مبلغ واقعی کسر نمی‌شود.
              </p>
            </form>
          )}
        </div>
      </div>
    </div>
  );
};

// ─────────────────────────────────────────────
// ORDERS PAGE (buyer's orders)
// ─────────────────────────────────────────────
const MyOrdersPage = () => {
  const [reviewOrder, setReviewOrder] = useState<OrderDetail | null>(null);

  const { data: orders, isLoading } = useGetMyOrdersQuery();

  // Full status map — all backend statuses with Persian labels + styling
  const statusConfig: Record<string, { label: string; color: string; icon: string }> = {
    PENDING_PAYMENT: { label: 'در انتظار تایید', color: 'bg-amber-50 text-amber-700 border-amber-200', icon: '⏳' },
    PAID: { label: 'تایید شده', color: 'bg-emerald-50 text-emerald-700 border-emerald-200', icon: '✅' },
    PICKED_UP: { label: 'انجام شده', color: 'bg-slate-100 text-slate-500 border-slate-200', icon: '🏁' },
    CANCELLED: { label: 'رد شده', color: 'bg-red-50 text-red-600 border-red-200', icon: '❌' },
  };

  if (isLoading) return (
    <div className="flex items-center justify-center h-64">
      <div className="w-10 h-10 rounded-full border-4 border-slate-200 border-t-emerald-500 animate-spin" />
    </div>
  );

  // Group by lifecycle phase
  const readyOrders = (orders || []).filter(o => o.status === 'PAID');              // تایید شده — show pickup code
  const pendingOrders = (orders || []).filter(o => o.status === 'PENDING_PAYMENT');   // در انتظار تایید
  const pastOrders = (orders || []).filter(o => ['PICKED_UP', 'CANCELLED'].includes(o.status)); // انجام شده / رد شده

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-black text-slate-800">📋 سفارش‌های من</h1>

      {/* ── Ready to pickup (تایید شده) ── */}
      {readyOrders.length > 0 && (
        <div>
          <p className="text-xs font-bold text-emerald-600 uppercase tracking-wide mb-3">✅ تایید شده — آماده دریافت</p>
          <div className="space-y-3">
            {readyOrders.map(order => {
              const cfg = statusConfig[order.status];
              return (
                <div key={order.id} className="bg-white rounded-3xl p-5 shadow-sm border border-emerald-100">
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center gap-3">
                      <div className="w-11 h-11 rounded-2xl bg-emerald-50 flex items-center justify-center text-xl shadow-sm">
                        {getCategoryEmoji(order.magic_bag_details?.category)}
                      </div>
                      <div>
                        <p className="font-black text-slate-800 text-sm">{order.magic_bag_details?.name}</p>
                        <p className="text-xs text-slate-400 mt-0.5">
                          {order.magic_bag_details?.store?.name ?? '👤 فروشنده حقیقی'}
                        </p>
                      </div>
                    </div>
                    <span className={`text-[10px] font-bold px-2.5 py-1 rounded-full border ${cfg.color}`}>{cfg.icon} {cfg.label}</span>
                  </div>
                  <div className="bg-emerald-50 rounded-2xl p-4 text-center border border-emerald-100">
                    <p className="text-xs text-emerald-600 font-semibold mb-1">کد تحویل شما</p>
                    <p className="text-2xl font-black tracking-[0.3em] text-emerald-800">{order.pickup_code}</p>
                    <p className="text-[10px] text-emerald-500 mt-1">این کد را به فروشنده نشان دهید</p>
                  </div>
                  <div className="flex justify-between text-xs font-semibold text-slate-500 mt-3 px-1">
                    <span>تعداد: {order.quantity} عدد</span>
                    <span className="font-black text-emerald-600">{parseFloat(order.total_price).toLocaleString()} ﷼</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* ── Pending (در انتظار تایید) ── */}
      {pendingOrders.length > 0 && (
        <div>
          <p className="text-xs font-bold text-amber-600 uppercase tracking-wide mb-3">⏳ در انتظار تایید</p>
          <div className="space-y-2">
            {pendingOrders.map(order => {
              const cfg = statusConfig[order.status];
              return (
                <div key={order.id} className="bg-white rounded-2xl px-4 py-4 shadow-sm border border-amber-100 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-amber-50 flex items-center justify-center text-lg shadow-sm">
                      {getCategoryEmoji(order.magic_bag_details?.category)}
                    </div>
                    <div>
                      <p className="font-bold text-slate-700 text-sm">{order.magic_bag_details?.name}</p>
                      <p className="text-[10px] text-slate-400">
                        {order.magic_bag_details?.store?.name ?? '👤 فروشنده حقیقی'} • {order.quantity} عدد • {parseFloat(order.total_price).toLocaleString()} ﷼
                      </p>
                    </div>
                  </div>
                  <span className={`text-[10px] font-bold px-2.5 py-1 rounded-full border ${cfg.color}`}>{cfg.label}</span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* ── Empty state ── */}
      {readyOrders.length === 0 && pendingOrders.length === 0 && pastOrders.length === 0 ? (
        <div className="bg-white rounded-3xl p-12 text-center shadow-sm border border-slate-100">
          <span className="text-5xl block mb-3">🛒</span>
          <h3 className="font-black text-slate-700">هنوز سفارشی ندارید</h3>
          <p className="text-xs text-slate-400 mt-1">از صفحه خانه کیسه جادویی سفارش دهید</p>
          <Link to="/app/discover" className="inline-block mt-4 px-6 py-2.5 bg-emerald-600 text-white rounded-xl font-bold text-sm shadow-md shadow-emerald-500/20 hover:bg-emerald-700 transition">
            رفتن به خانه
          </Link>
        </div>
      ) : pastOrders.length > 0 && (
        <div>
          <p className="text-xs font-bold text-slate-400 uppercase tracking-wide mb-3">سوابق سفارش‌ها</p>
          <div className="space-y-2">
            {pastOrders.map(order => {
              const cfg = statusConfig[order.status] || statusConfig.CANCELLED;
              return (
                <div key={order.id} className="bg-white rounded-2xl px-4 py-3 shadow-sm border border-slate-100">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="w-9 h-9 rounded-xl bg-slate-50 flex items-center justify-center text-base shadow-sm">
                        {getCategoryEmoji(order.magic_bag_details?.category)}
                      </div>
                      <div>
                        <p className="font-bold text-slate-700 text-sm">{order.magic_bag_details?.name}</p>
                        <p className="text-[10px] text-slate-400">
                          {order.magic_bag_details?.store?.name ?? '👤 فروشنده حقیقی'} • {order.quantity} عدد • {parseFloat(order.total_price).toLocaleString()} ﷼
                        </p>
                      </div>
                    </div>
                    <span className={`text-[10px] font-bold px-2.5 py-1 rounded-full border ${cfg.color}`}>{cfg.icon} {cfg.label}</span>
                  </div>
                  {order.status === 'PICKED_UP' && (
                    <div className="mt-3 pt-3 border-t border-slate-50">
                      {order.my_review ? (
                        <div className="flex items-center gap-2">
                          <span className="text-[10px] font-bold text-slate-400">امتیاز شما:</span>
                          <StarRatingDisplay rating={order.my_review.rating} />
                          {order.my_review.comment && (
                            <span className="text-[10px] text-slate-500 truncate">— {order.my_review.comment}</span>
                          )}
                        </div>
                      ) : (
                        <button
                          onClick={() => setReviewOrder(order)}
                          className="w-full py-2 rounded-xl text-xs font-black bg-amber-50 text-amber-700 border border-amber-200 hover:bg-amber-100 transition"
                        >
                          ⭐ ثبت امتیاز
                        </button>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}
      <SubmitReviewModal order={reviewOrder} onClose={() => setReviewOrder(null)} />
    </div>
  );
};

// ─────────────────────────────────────────────
// SHOP PAGE (seller management, conditional)
// ─────────────────────────────────────────────
const ShopPage = () => {
  const { data: store, isLoading } = useGetMyStoreQuery();
  const [vendorMode, setVendorMode] = useState<'individual' | 'register_store'>('individual');
  const [activeTab, setActiveTab] = useState<'bags' | 'orders' | 'profile'>('bags');

  const hasStore = !!store;

  useEffect(() => {
    if (hasStore) {
      setActiveTab('profile');
    }
  }, [hasStore]);

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-40">
        <div className="w-10 h-10 rounded-full border-4 border-slate-200 border-t-emerald-500 animate-spin" />
      </div>
    );
  }

  if (hasStore) {
    const tabs = [
      { key: 'profile' as const, label: '🏪 فروشگاه', },
      { key: 'bags' as const, label: '🎁 کیسه‌ها', },
      { key: 'orders' as const, label: '📦 سفارشات', },
    ];
    return (
      <div className="space-y-4">
        <h1 className="text-xl font-black text-slate-800">🏪 فروشگاه من</h1>
        <div className="bg-white rounded-2xl p-1.5 shadow-sm border border-slate-100 flex gap-1">
          {tabs.map(t => (
            <button
              key={t.key}
              onClick={() => setActiveTab(t.key)}
              className={`flex-1 py-2.5 text-xs font-black rounded-xl transition-all ${activeTab === t.key
                ? 'bg-emerald-600 text-white shadow-md shadow-emerald-500/20'
                : 'text-slate-500 hover:bg-slate-50'
                }`}
            >
              {t.label}
            </button>
          ))}
        </div>
        {activeTab === 'profile' && <StoreProfilePage />}
        {activeTab === 'bags' && <InventoryPage />}
        {activeTab === 'orders' && <VendorOrdersPage />}
      </div>
    );
  }

  return (
    <div className="space-y-4" dir="rtl">
      <h1 className="text-xl font-black text-slate-800">💼 فروش محصولات</h1>

      <div className="grid grid-cols-2 gap-2 bg-slate-100 p-1.5 rounded-2xl border border-slate-200/50">
        <button
          onClick={() => setVendorMode('individual')}
          className={`py-3 text-xs font-black rounded-xl transition-all flex items-center justify-center gap-1.5 ${vendorMode === 'individual'
            ? 'bg-white text-emerald-800 shadow-sm border border-emerald-100'
            : 'text-slate-500 hover:text-slate-800'
            }`}
        >
          👤 فروش به عنوان شخص حقیقی
        </button>
        <button
          onClick={() => setVendorMode('register_store')}
          className={`py-3 text-xs font-black rounded-xl transition-all flex items-center justify-center gap-1.5 ${vendorMode === 'register_store'
            ? 'bg-white text-emerald-800 shadow-sm border border-emerald-100'
            : 'text-slate-500 hover:text-slate-800'
            }`}
        >
          🏪 ثبت‌نام فروشگاه حقوقی
        </button>
      </div>

      {vendorMode === 'register_store' ? (
        <StoreProfilePage />
      ) : (
        <div className="space-y-4">
          <div className="bg-white rounded-2xl p-1.5 shadow-sm border border-slate-100 flex gap-1">
            <button
              onClick={() => setActiveTab('bags')}
              className={`flex-1 py-2.5 text-xs font-black rounded-xl transition-all ${activeTab === 'bags'
                ? 'bg-emerald-600 text-white shadow-md shadow-emerald-500/20'
                : 'text-slate-500 hover:bg-slate-50'
                }`}
            >
              🎁 محصولات من
            </button>
            <button
              onClick={() => setActiveTab('orders')}
              className={`flex-1 py-2.5 text-xs font-black rounded-xl transition-all ${activeTab === 'orders'
                ? 'bg-emerald-600 text-white shadow-md shadow-emerald-500/20'
                : 'text-slate-500 hover:bg-slate-50'
                }`}
            >
              📦 سفارشات دریافتی
            </button>
          </div>

          {activeTab === 'bags' && <InventoryPage />}
          {activeTab === 'orders' && <VendorOrdersPage />}
        </div>
      )}
    </div>
  );
};

// Store profile (embedded inside ShopPage)
const StoreProfilePage = () => {
  const { data: store, isLoading, refetch } = useGetMyStoreQuery();
  const [updateStore, { isLoading: isUpdating }] = useUpdateStoreMutation();

  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [address, setAddress] = useState('');
  const [lat, setLat] = useState(35.6892);
  const [lng, setLng] = useState(51.3890);
  const [statusMsg, setStatusMsg] = useState('');
  const [success, setSuccess] = useState(false);
  const [showMap, setShowMap] = useState(false);

  useEffect(() => {
    if (store) {
      setName(store.name);
      setDescription(store.description);
      setAddress(store.address);
      setLat(parseFloat(String(store.latitude)));
      setLng(parseFloat(String(store.longitude)));
    }
  }, [store]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setStatusMsg(''); setSuccess(false);
    try {
      await updateStore({ name, description, address, latitude: parseFloat(lat.toFixed(6)), longitude: parseFloat(lng.toFixed(6)), status: 'APPROVED' }).unwrap();
      setSuccess(true); refetch();
    } catch (err: any) {
      setStatusMsg('خطا در ذخیره اطلاعات فروشگاه.');
    }
  };

  if (isLoading) return <div className="flex justify-center items-center h-40"><div className="w-10 h-10 rounded-full border-4 border-slate-200 border-t-emerald-500 animate-spin" /></div>;

  return (
    <div className="bg-white rounded-3xl p-5 shadow-sm border border-slate-100">
      {store && (
        <div className={`mb-4 px-3 py-2 rounded-xl text-xs font-bold border ${store.status === 'APPROVED' ? 'bg-emerald-50 text-emerald-700 border-emerald-100' :
          store.status === 'REJECTED' ? 'bg-red-50 text-red-600 border-red-100' :
            'bg-amber-50 text-amber-700 border-amber-100'
          }`}>
          {store.status === 'APPROVED' ? '✔️ فروشگاه تایید شده' :
            store.status === 'REJECTED' ? '❌ فروشگاه رد شده' : '⏳ در انتظار بررسی'}
        </div>
      )}
      {success && <div className="mb-4 p-3 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-700 text-sm font-bold text-center">✅ تغییرات ذخیره شد!</div>}
      {statusMsg && <div className="mb-4 p-3 rounded-xl bg-red-50 border border-red-200 text-red-600 text-sm font-bold">{statusMsg}</div>}

      <form className="space-y-4" onSubmit={handleSubmit}>
        <div>
          <label className="block text-xs font-bold text-slate-500 mb-2">نام فروشگاه</label>
          <input type="text" required value={name} onChange={e => setName(e.target.value)}
            className="w-full px-4 py-3 rounded-xl bg-slate-50 border border-slate-200 focus:outline-none focus:border-emerald-500 focus:bg-white text-sm transition"
            placeholder="مثال: نانوایی برکت" />
        </div>
        <div>
          <label className="block text-xs font-bold text-slate-500 mb-2">توضیحات</label>
          <textarea value={description} onChange={e => setDescription(e.target.value)}
            className="w-full px-4 py-3 rounded-xl bg-slate-50 border border-slate-200 focus:outline-none focus:border-emerald-500 focus:bg-white text-sm h-20 resize-none transition"
            placeholder="درباره فروشگاه توضیح دهید..." />
        </div>
        <div>
          <label className="block text-xs font-bold text-slate-500 mb-2">آدرس</label>
          <textarea required value={address} onChange={e => setAddress(e.target.value)}
            className="w-full px-4 py-3 rounded-xl bg-slate-50 border border-slate-200 focus:outline-none focus:border-emerald-500 focus:bg-white text-sm h-16 resize-none transition"
            placeholder="تهران، میدان ونک..." />
        </div>

        {/* Location */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <label className="text-xs font-bold text-slate-500">موقعیت روی نقشه</label>
            <button type="button" onClick={() => setShowMap(v => !v)}
              className="text-xs px-3 py-1.5 rounded-lg bg-emerald-50 text-emerald-700 hover:bg-emerald-100 font-bold transition">
              {showMap ? '🗺️ بستن نقشه' : '🗺️ انتخاب از نقشه'}
            </button>
          </div>
          <div className="flex gap-2 mb-2">
            <div className="flex-1 px-3 py-2 rounded-xl bg-slate-50 border border-slate-200 text-xs font-mono text-slate-600">
              <span className="text-slate-400 text-[10px] block mb-0.5">عرض</span>{lat.toFixed(6)}
            </div>
            <div className="flex-1 px-3 py-2 rounded-xl bg-slate-50 border border-slate-200 text-xs font-mono text-slate-600">
              <span className="text-slate-400 text-[10px] block mb-0.5">طول</span>{lng.toFixed(6)}
            </div>
          </div>
          {showMap && (
            <div className="h-64 rounded-2xl overflow-hidden border border-emerald-200">
              <LocationPicker initialPosition={{ lat, lng }} onLocationSelect={(a, b) => { setLat(a); setLng(b); }} />
            </div>
          )}
        </div>

        <button type="submit" disabled={isUpdating}
          className="w-full py-3.5 rounded-xl font-black bg-emerald-600 text-white shadow-md shadow-emerald-500/20 hover:brightness-105 active:scale-[0.98] transition-all disabled:opacity-50">
          {isUpdating ? '⏳ در حال ذخیره...' : '💾 ذخیره تغییرات'}
        </button>
      </form>
    </div>
  );
};

// Inventory / bags management
const InventoryPage = () => {
  const { data: bagsData, isLoading, refetch } = useGetBagsQuery();
  const [modalOpen, setModalOpen] = useState(false);
  const bagsList = bagsData?.results || [];

  if (isLoading) return <div className="flex justify-center items-center h-40"><div className="w-10 h-10 rounded-full border-4 border-slate-200 border-t-emerald-500 animate-spin" /></div>;

  return (
    <div className="space-y-4" dir="rtl">
      <div className="flex items-center justify-between">
        <p className="text-sm font-bold text-slate-600">{bagsList.length} محصول ثبت‌شده</p>
        <button onClick={() => setModalOpen(true)}
          className="px-4 py-2 rounded-xl font-black text-sm bg-emerald-600 text-white shadow-md shadow-emerald-500/20 hover:bg-emerald-700 transition">
          ➕ محصول جدید
        </button>
      </div>

      {bagsList.length === 0 ? (
        <div className="bg-white rounded-3xl p-10 text-center shadow-sm border border-slate-100">
          <span className="text-5xl block mb-3">🎁</span>
          <h3 className="font-black text-slate-700">هیچ محصولی ثبت نشده</h3>
          <p className="text-xs text-slate-400 mt-1">اولین محصول خود را اضافه کنید</p>
        </div>
      ) : (
        <div className="space-y-3">
          {bagsList.map(bag => (
            <div key={bag.id} className="bg-white rounded-2xl p-4 shadow-sm border border-slate-100">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 rounded-xl bg-slate-50 flex items-center justify-center text-2xl shadow-inner">
                    {getCategoryEmoji(bag.category)}
                  </div>
                  <div>
                    <p className="font-black text-slate-700 text-sm">
                      {bag.name || 'کیسه جادویی'} <span className="text-xs text-slate-400 font-normal">({bag.quantity} عدد)</span>
                    </p>
                    {bag.description && (
                      <p className="text-xs text-slate-400 mt-0.5">{bag.description}</p>
                    )}
                    <p className="text-xs text-slate-500 font-mono mt-1" dir="ltr font-semibold">
                      ⏰ {bag.pickup_start_time.slice(0, 5)} – {bag.pickup_end_time.slice(0, 5)}
                    </p>
                  </div>
                </div>
                <div className="text-left">
                  <p className="text-[10px] text-slate-400 line-through">{parseFloat(bag.original_price).toLocaleString()} ﷼</p>
                  <p className="text-sm font-black text-emerald-600">{parseFloat(bag.platform_price).toLocaleString()} ﷼</p>
                </div>
              </div>
              <div className="mt-3 flex items-center justify-between pt-2 border-t border-slate-50">
                <span className="text-[10px] font-bold text-slate-500 bg-slate-50 px-2.5 py-0.5 rounded-md">
                  {categories.find(c => c.value === bag.category)?.label || bag.category}
                </span>
                {bag.is_active
                  ? <span className="text-[10px] font-bold bg-emerald-50 text-emerald-600 border border-emerald-100 px-2.5 py-0.5 rounded-full">● فعال</span>
                  : <span className="text-[10px] font-bold bg-slate-100 text-slate-400 px-2.5 py-0.5 rounded-full">غیرفعال</span>
                }
              </div>
            </div>
          ))}
        </div>
      )}

      <CreateBagModal isOpen={modalOpen} onClose={() => setModalOpen(false)} onRefresh={refetch} />
    </div>
  );
};

// Catalog Explorer UI
const CatalogExplorer = ({ onSelect, onBack }: { onSelect: (product: any) => void, onBack: () => void }) => {
  const { data: sources, isLoading: loadingSources } = useGetCatalogSourcesQuery();
  const [selectedSource, setSelectedSource] = useState<string>('');
  
  const { data: categories, isLoading: loadingCategories } = useGetCatalogCategoriesQuery(selectedSource, { skip: !selectedSource });
  const [selectedCategory, setSelectedCategory] = useState<string>('');

  const [page, setPage] = useState(1);
  const { data: productsData, isLoading: loadingProducts, isFetching } = useGetCatalogProductsQuery(
    { source: selectedSource, category: selectedCategory, page },
    { skip: !selectedSource || !selectedCategory }
  );

  useEffect(() => {
    if (sources && sources.length > 0 && !selectedSource) {
      setSelectedSource(sources[0]);
    }
  }, [sources, selectedSource]);

  return (
    <div className="w-full flex flex-col h-full absolute inset-0 bg-slate-50 z-20 rounded-3xl overflow-hidden shadow-2xl animate-in slide-in-from-bottom-8 duration-300" dir="rtl">
        {/* Header */}
        <div className="bg-white border-b border-slate-200 px-5 py-4 flex items-center justify-between shadow-sm z-10 sticky top-0 shrink-0">
          <h3 className="text-lg font-black text-slate-800">🛒 جستجو در کاتالوگ</h3>
          <button type="button" onClick={onBack} className="text-xs px-4 py-2 font-bold bg-slate-100 text-slate-600 hover:bg-slate-200 rounded-xl transition shrink-0">
            بازگشت به فرم
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-5 relative custom-scrollbar">
          
          {/* Sources Dropdown */}
          <div className="mb-6 bg-white p-4 rounded-2xl shadow-sm border border-slate-100">
            <label className="block text-xs font-bold text-slate-500 mb-2">منبع کاتالوگ</label>
            <div className="flex gap-2 overflow-x-auto pb-2 custom-scrollbar hide-scrollbar">
              {loadingSources ? <div className="text-xs text-slate-400">در حال بارگذاری...</div> : 
               sources?.map(s => (
                <button key={s} type="button" onClick={() => { setSelectedSource(s); setSelectedCategory(''); setPage(1); }}
                  className={`px-4 py-2 rounded-xl text-sm font-bold whitespace-nowrap transition-all ${
                    selectedSource === s ? 'bg-emerald-600 text-white shadow-md shadow-emerald-500/20' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                  }`}>
                  {s === 'snappmarket' ? 'اسنپ‌مارکت' : s}
                </button>
              ))}
            </div>
          </div>

          {/* Categories Grid */}
          {selectedSource && (
            <div className="mb-6">
              <label className="block text-xs font-bold text-slate-500 mb-3 px-1">دسته‌بندی‌ها</label>
              <div className="flex flex-wrap gap-2">
                {loadingCategories ? <div className="text-xs text-slate-400 px-1">در حال بارگذاری دسته‌ها...</div> :
                 categories?.map(c => (
                  <button key={c} type="button" onClick={() => { setSelectedCategory(c); setPage(1); }}
                    className={`px-4 py-2 rounded-xl text-xs font-bold transition-all border ${
                      selectedCategory === c ? 'bg-emerald-50 border-emerald-500 text-emerald-700 shadow-sm' : 'bg-white border-slate-200 text-slate-600 hover:border-emerald-300 hover:bg-emerald-50/50'
                    }`}>
                    {c}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Products Grid */}
          {selectedCategory && (
            <div>
              <div className="flex items-center justify-between mb-4 px-1">
                 <label className="text-sm font-black text-slate-800">محصولات ({productsData?.count || 0})</label>
                 {isFetching && <span className="text-[10px] text-emerald-600 font-bold bg-emerald-50 px-2 py-1 rounded-md animate-pulse">در حال بروزرسانی...</span>}
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                {loadingProducts && !productsData ? (
                  Array.from({ length: 4 }).map((_, i) => (
                    <div key={i} className="bg-white rounded-2xl p-3 border border-slate-100 animate-pulse h-40"></div>
                  ))
                ) : productsData?.results?.map((p: any) => (
                  <div key={p.id} onClick={() => onSelect(p)} 
                    className="bg-white rounded-2xl p-3 border border-slate-100 shadow-sm hover:shadow-md hover:border-emerald-300 transition-all cursor-pointer group flex flex-col justify-between overflow-hidden">
                    <div className="aspect-square bg-slate-50 rounded-xl mb-3 overflow-hidden flex items-center justify-center relative">
                      {p.image_url ? 
                        <img src={p.image_url} alt={p.title} className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500" /> : 
                        <span className="text-2xl opacity-20">📦</span>
                      }
                      <div className="absolute inset-0 bg-emerald-900/0 group-hover:bg-emerald-900/10 transition-colors"></div>
                    </div>
                    <div className="text-xs font-bold text-slate-700 line-clamp-2 leading-relaxed mb-1">{p.title}</div>
                    {p.brand && <div className="text-[9px] font-bold text-slate-400">{p.brand}</div>}
                  </div>
                ))}
              </div>

              {/* Pagination */}
              {productsData && productsData.count > 20 && (
                <div className="flex items-center justify-center gap-4 mt-8 pb-4">
                  <button type="button" disabled={page === 1} onClick={() => setPage(p => p - 1)}
                    className="w-10 h-10 rounded-full flex items-center justify-center bg-white border border-slate-200 text-slate-600 disabled:opacity-30 font-bold hover:bg-slate-50 hover:text-emerald-600 transition">
                    →
                  </button>
                  <span className="text-xs font-bold text-slate-500">صفحه {page}</span>
                  <button type="button" disabled={page * 20 >= productsData.count} onClick={() => setPage(p => p + 1)}
                    className="w-10 h-10 rounded-full flex items-center justify-center bg-white border border-slate-200 text-slate-600 disabled:opacity-30 font-bold hover:bg-slate-50 hover:text-emerald-600 transition">
                    ←
                  </button>
                </div>
              )}
            </div>
          )}
          
        </div>
    </div>
  );
};

// Create bag modal
const CreateBagModal = ({ isOpen, onClose, onRefresh }: { isOpen: boolean; onClose: () => void; onRefresh: () => void }) => {
  const { data: store } = useGetMyStoreQuery();
  const hasStore = !!store;

  const { data: addresses } = useGetMyAddressesQuery();
  const activeAddress = addresses?.find(a => a.is_active);

  const [createBag, { isLoading }] = useCreateBagMutation();
  const [qty, setQty] = useState(5);
  const [originalPrice, setOriginalPrice] = useState('100000');
  const [platformPrice, setPlatformPrice] = useState('30000');
  const [startTime, setStartTime] = useState('18:00');
  const [endTime, setEndTime] = useState('20:00');
  const [name, setName] = useState('کیسه جادویی');
  const [description, setDescription] = useState('');
  const [category, setCategory] = useState('FOODS');
  const [lat, setLat] = useState(35.6892);
  const [lng, setLng] = useState(51.3890);
  const [showMap, setShowMap] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [expiryImageFile, setExpiryImageFile] = useState<File | null>(null);

  const [showExplorer, setShowExplorer] = useState(false);

  useEffect(() => {
    if (isOpen) {
      setName('کیسه جادویی');
      setDescription('');
      setCategory('FOODS');
      setQty(5);
      setOriginalPrice('100000');
      setPlatformPrice('30000');
      setStartTime('18:00');
      setEndTime('20:00');
      setShowMap(false);
      setErrorMsg('');
      setImageFile(null);
      setExpiryImageFile(null);
      setShowExplorer(false);
      if (activeAddress) {
        setLat(parseFloat(activeAddress.latitude));
        setLng(parseFloat(activeAddress.longitude));
      } else {
        setLat(35.6892);
        setLng(51.3890);
      }
    }
  }, [isOpen, activeAddress]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault(); setErrorMsg('');
    const hasImage = imageFile || (window as any)._selectedCatalogImage;
    if (!hasImage || !expiryImageFile) {
      setErrorMsg('لطفاً هم تصویر محصول و هم تصویر برچسب انقضا را بارگذاری کنید.');
      return;
    }
    const formData = new FormData();
    formData.append('name', name);
    formData.append('description', description);
    formData.append('category', category);
    formData.append('original_price', parseFloat(originalPrice).toFixed(2));
    formData.append('platform_price', parseFloat(platformPrice).toFixed(2));
    formData.append('quantity', qty.toString());
    formData.append('pickup_start_time', startTime + ':00');
    formData.append('pickup_end_time', endTime + ':00');
    if (imageFile) formData.append('image', imageFile);
    if ((window as any)._selectedCatalogImage && !imageFile) formData.append('catalog_image_url', (window as any)._selectedCatalogImage);
    formData.append('expiry_image', expiryImageFile);
    if (!hasStore) {
      formData.append('latitude', lat.toString());
      formData.append('longitude', lng.toString());
    }
    try {
      await createBag(formData).unwrap();
      onRefresh(); onClose();
    } catch (err: any) {
      setErrorMsg(err.data?.detail || 'خطا در ثبت محصول.');
    }
  };

  const selectCatalogProduct = (product: any) => {
    setName(product.title);
    if (product.description) setDescription(product.description);
    if (product.image_url) (window as any)._selectedCatalogImage = product.image_url;
    setShowExplorer(false);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-black/40 backdrop-blur-sm px-4 pb-4" dir="rtl">
      <div className="w-full max-w-sm bg-white rounded-3xl p-6 shadow-2xl max-h-[90vh] overflow-hidden relative flex flex-col">
        {showExplorer && <CatalogExplorer onSelect={selectCatalogProduct} onBack={() => setShowExplorer(false)} />}
        
        <div className="overflow-y-auto custom-scrollbar pr-1 pb-1">
          <div className="flex items-center justify-between mb-5">
            <h3 className="text-lg font-black text-slate-800">🎁 محصول جدید</h3>
            <button onClick={onClose} className="w-9 h-9 flex items-center justify-center rounded-full bg-slate-100 text-slate-500 hover:bg-slate-200 transition font-bold">✕</button>
          </div>
          
          {/* Catalog Browse Button */}
          <div className="mb-6">
              <button type="button" onClick={() => setShowExplorer(true)}
                className="w-full flex items-center justify-center gap-2 px-4 py-3.5 rounded-xl bg-emerald-50 text-emerald-700 hover:bg-emerald-100 border border-emerald-200 transition font-bold shadow-sm group">
                <span className="text-lg group-hover:scale-110 transition-transform">🛒</span> 
                انتخاب از کاتالوگ جامع محصولات
              </button>
              <p className="text-[10px] text-slate-400 font-bold text-center mt-2 px-4">با انتخاب از کاتالوگ، نام و تصویر محصول به‌طور خودکار پر می‌شود.</p>
          </div>

        {errorMsg && <div className="mb-4 p-3 rounded-xl bg-red-50 border border-red-200 text-red-600 text-xs font-bold">⚠️ {errorMsg}</div>}
        <form className="space-y-4" onSubmit={handleSubmit}>
          <div>
            <label className="block text-xs font-bold text-slate-500 mb-1.5">نام محصول</label>
            <input type="text" required value={name} onChange={e => setName(e.target.value)}
              className="w-full px-3 py-3 rounded-xl bg-slate-50 border border-slate-200 focus:outline-none focus:border-emerald-500 text-sm transition"
              placeholder="مثال: کیسه سبزی تازه یا غذای روز" />
          </div>
          <div>
            <label className="block text-xs font-bold text-slate-500 mb-1.5">توضیحات</label>
            <textarea value={description} onChange={e => setDescription(e.target.value)}
              className="w-full px-3 py-2 rounded-xl bg-slate-50 border border-slate-200 focus:outline-none focus:border-emerald-500 text-sm h-16 resize-none transition"
              placeholder="توضیح کوتاهی درباره محصول..." />
          </div>
          <div>
            <label className="block text-xs font-bold text-slate-500 mb-1.5">دسته‌بندی</label>
            <select value={category} onChange={e => setCategory(e.target.value)}
              className="w-full px-3 py-3 rounded-xl bg-slate-50 border border-slate-200 focus:outline-none focus:border-emerald-500 text-sm transition font-bold text-slate-700">
              {categories.map(c => (
                <option key={c.value} value={c.value}>{c.label}</option>
              ))}
            </select>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-bold text-slate-500 mb-1.5">تعداد</label>
              <input type="number" required min={1} value={qty} onChange={e => setQty(parseInt(e.target.value))}
                className="w-full px-3 py-3 rounded-xl bg-slate-50 border border-slate-200 focus:outline-none focus:border-emerald-500 text-center font-black text-sm transition" />
            </div>
            <div>
              <label className="block text-xs font-bold text-slate-500 mb-1.5">قیمت اصلی (﷼)</label>
              <input type="number" required value={originalPrice} onChange={e => setOriginalPrice(e.target.value)}
                className="w-full px-3 py-3 rounded-xl bg-slate-50 border border-slate-200 focus:outline-none focus:border-emerald-500 text-center font-black text-sm transition" />
            </div>
          </div>
          <div className="grid grid-cols-3 gap-3">
            <div>
              <label className="block text-xs font-bold text-slate-500 mb-1.5">قیمت فروش</label>
              <input type="number" required value={platformPrice} onChange={e => setPlatformPrice(e.target.value)}
                className="w-full px-3 py-3 rounded-xl bg-slate-50 border border-slate-200 focus:outline-none focus:border-emerald-500 text-center font-black text-sm transition" />
            </div>
            <div>
              <label className="block text-xs font-bold text-slate-500 mb-1.5">شروع</label>
              <input type="time" required value={startTime} onChange={e => setStartTime(e.target.value)}
                className="w-full px-2 py-3 rounded-xl bg-slate-50 border border-slate-200 focus:outline-none focus:border-emerald-500 text-center font-mono text-xs transition" />
            </div>
            <div>
              <label className="block text-xs font-bold text-slate-500 mb-1.5">پایان</label>
              <input type="time" required value={endTime} onChange={e => setEndTime(e.target.value)}
                className="w-full px-2 py-3 rounded-xl bg-slate-50 border border-slate-200 focus:outline-none focus:border-emerald-500 text-center font-mono text-xs transition" />
            </div>
          </div>

          {!hasStore && (
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="text-xs font-bold text-slate-500">موقعیت محصول روی نقشه</label>
                <button type="button" onClick={() => setShowMap(v => !v)}
                  className="text-xs px-3 py-1.5 rounded-lg bg-emerald-50 text-emerald-700 hover:bg-emerald-100 font-bold transition">
                  {showMap ? '🗺️ بستن نقشه' : '🗺️ انتخاب از نقشه'}
                </button>
              </div>
              <div className="flex gap-2 mb-2">
                <div className="flex-1 px-3 py-2 rounded-xl bg-slate-50 border border-slate-200 text-xs font-mono text-slate-600">
                  <span className="text-slate-400 text-[10px] block mb-0.5">عرض</span>{lat.toFixed(6)}
                </div>
                <div className="flex-1 px-3 py-2 rounded-xl bg-slate-50 border border-slate-200 text-xs font-mono text-slate-600">
                  <span className="text-slate-400 text-[10px] block mb-0.5">طول</span>{lng.toFixed(6)}
                </div>
              </div>
              {showMap && (
                <div className="h-48 rounded-2xl overflow-hidden border border-emerald-200">
                  <LocationPicker initialPosition={{ lat, lng }} onLocationSelect={(a, b) => { setLat(a); setLng(b); }} />
                </div>
              )}
            </div>
          )}

          <div className="grid grid-cols-2 gap-3 mb-4">
            <div>
              <label className="block text-xs font-bold text-slate-500 mb-1.5">📸 تصویر محصول</label>
              <input type="file" required={!(window as any)._selectedCatalogImage} accept="image/*" onChange={e => setImageFile(e.target.files?.[0] || null)}
                className="w-full text-xs text-slate-500 file:mr-2 file:py-2 file:px-3 file:rounded-xl file:border-0 file:text-[10px] file:font-black file:bg-emerald-50 file:text-emerald-700 hover:file:bg-emerald-100 transition cursor-pointer" />
              {(window as any)._selectedCatalogImage && !imageFile && <div className="text-[10px] text-emerald-600 mt-1 font-bold">✓ تصویر از کاتالوگ انتخاب شد</div>}
            </div>
            <div>
              <label className="block text-xs font-bold text-slate-500 mb-1.5">🔍 برچسب انقضا</label>
              <input type="file" required accept="image/*" onChange={e => setExpiryImageFile(e.target.files?.[0] || null)}
                className="w-full text-xs text-slate-500 file:mr-2 file:py-2 file:px-3 file:rounded-xl file:border-0 file:text-[10px] file:font-black file:bg-emerald-50 file:text-emerald-700 hover:file:bg-emerald-100 transition cursor-pointer" />
            </div>
          </div>

          <div className="flex gap-3 pt-2">
            <button type="submit" disabled={isLoading}
              className="flex-1 py-3.5 rounded-xl font-black bg-emerald-600 text-white shadow-md shadow-emerald-500/20 hover:brightness-105 active:scale-[0.98] transition-all disabled:opacity-50">
              {isLoading ? '⏳ ثبت...' : '✅ ثبت محصول'}
            </button>
            <button type="button" onClick={onClose} className="px-5 py-3.5 rounded-xl font-bold border border-slate-200 text-slate-600 hover:bg-slate-50 transition">
              انصراف
            </button>
          </div>
        </form>
        </div>
      </div>
    </div>
  );
};


// Vendor orders
const VendorOrdersPage = () => {
  const { data: orders, isLoading, refetch } = useGetVendorOrdersQuery();
  const [verifyPickup, { isLoading: isVerifying }] = useVerifyPickupMutation();
  const [approveOrder, { isLoading: isApproving }] = useApproveOrderMutation();
  const [rejectOrder, { isLoading: isRejecting }] = useRejectOrderMutation();

  const [code, setCode] = useState('');
  const [errorMsg, setErrorMsg] = useState('');
  const [successMsg, setSuccessMsg] = useState('');
  const [actionError, setActionError] = useState<string | null>(null);

  const handleVerify = async (e: React.FormEvent) => {
    e.preventDefault(); setErrorMsg(''); setSuccessMsg(''); setActionError(null);
    const clean = code.trim().toUpperCase();
    if (clean.length !== 6) { setErrorMsg('کد باید ۶ رقمی باشد.'); return; }
    const match = orders?.find(o => o.pickup_code === clean);
    if (!match) { setErrorMsg('سفارشی با این کد یافت نشد.'); return; }
    if (match.status === 'PICKED_UP') { setErrorMsg('این سفارش قبلاً تحویل داده شده.'); return; }
    try {
      await verifyPickup({ orderId: match.id, pickup_code: clean }).unwrap();
      setSuccessMsg(`سفارش #${match.id} تحویل داده شد ✅`);
      setCode('');
      refetch();
    } catch (err: any) {
      setErrorMsg(err.data?.error || 'خطا در ثبت تحویل.');
    }
  };

  const handleApprove = async (orderId: number) => {
    setErrorMsg(''); setSuccessMsg(''); setActionError(null);
    try {
      await approveOrder(orderId).unwrap();
      setSuccessMsg(`سفارش #${orderId} با موفقیت تایید شد ✅`);
      refetch();
    } catch (err: any) {
      setActionError(err.data?.error || 'خطا در تایید سفارش.');
    }
  };

  const handleReject = async (orderId: number) => {
    setErrorMsg(''); setSuccessMsg(''); setActionError(null);
    try {
      await rejectOrder(orderId).unwrap();
      setSuccessMsg(`سفارش #${orderId} لغو و رد شد ❌`);
      refetch();
    } catch (err: any) {
      setActionError(err.data?.error || 'خطا در رد سفارش.');
    }
  };

  if (isLoading) return (
    <div className="flex justify-center items-center h-40">
      <div className="w-10 h-10 rounded-full border-4 border-slate-200 border-t-emerald-500 animate-spin" />
    </div>
  );

  const ordersList = orders || [];
  const pendingOrders = ordersList.filter(o => o.status === 'PENDING_PAYMENT');
  const activeOrders = ordersList.filter(o => o.status === 'PAID');
  const historyOrders = ordersList.filter(o => ['PICKED_UP', 'CANCELLED'].includes(o.status));

  return (
    <div className="space-y-6" dir="rtl">
      <h1 className="text-xl font-black text-slate-800">🏪 مدیریت سفارش‌های فروشگاه</h1>

      {actionError && (
        <div className="p-3 rounded-xl bg-red-50 border border-red-200 text-red-600 text-xs font-bold">
          {actionError}
        </div>
      )}

      {/* Pickup scanner */}
      <div className="bg-white rounded-3xl p-5 shadow-sm border border-slate-100">
        <div className="flex items-center gap-2 mb-3">
          <span className="text-xl">⚡</span>
          <p className="text-sm font-black text-slate-700">تایید تحویل با کد تحویل خریدار</p>
        </div>
        {successMsg && <div className="mb-3 p-3 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-700 text-xs font-bold">{successMsg}</div>}
        {errorMsg && <div className="mb-3 p-3 rounded-xl bg-red-50 border border-red-200 text-red-600 text-xs font-bold">{errorMsg}</div>}
        <form onSubmit={handleVerify} className="flex gap-2">
          <input
            type="text"
            required
            maxLength={6}
            placeholder="کد ۶ رقمی تحویل"
            value={code}
            onChange={e => setCode(e.target.value)}
            className="flex-1 px-4 py-3 rounded-xl border border-slate-200 focus:outline-none focus:border-emerald-500 text-center font-black tracking-widest text-lg uppercase bg-slate-50 transition"
          />
          <button
            type="submit"
            disabled={isVerifying}
            className="px-6 py-3 rounded-xl font-black bg-emerald-600 text-white shadow-md shadow-emerald-500/20 hover:brightness-105 transition disabled:opacity-50"
          >
            {isVerifying ? '...' : 'تایید'}
          </button>
        </form>
      </div>

      {/* ── Pending Orders Section (در انتظار تایید) ── */}
      {pendingOrders.length > 0 && (
        <div className="space-y-3">
          <p className="text-xs font-bold text-amber-600 uppercase tracking-wide">⏳ سفارش‌های در انتظار تایید ({pendingOrders.length})</p>
          <div className="space-y-3">
            {pendingOrders.map(order => (
              <div key={order.id} className="bg-white rounded-3xl p-5 shadow-sm border border-amber-200/60 relative overflow-hidden">
                <div className="absolute top-0 right-0 left-0 h-1.5 bg-amber-400" />
                <div className="flex items-start justify-between">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-black text-slate-800">سفارش #{order.id}</span>
                      <span className="text-[10px] bg-amber-50 text-amber-700 border border-amber-100 px-2 py-0.5 rounded-full font-bold">در انتظار تایید</span>
                    </div>
                    <p className="text-xs text-slate-500 mt-2 font-semibold">
                      👤 خریدار: {order.customer_details?.first_name || order.customer_details?.last_name
                        ? `${order.customer_details.first_name || ''} ${order.customer_details.last_name || ''}`.trim()
                        : 'کاربر برکت'} ({order.customer_details?.phone_number || `شناسه: ${order.customer}`})
                    </p>
                    <p className="text-xs text-slate-400 mt-1">تعداد کیسه: {order.quantity}</p>
                  </div>
                  <div className="text-left">
                    <p className="text-sm font-black text-emerald-600">{parseFloat(order.total_price).toLocaleString()} ﷼</p>
                    <p className="text-[10px] text-slate-400 mt-1">
                      {new Date(order.created_at).toLocaleTimeString('fa-IR', { hour: '2-digit', minute: '2-digit' })}
                    </p>
                  </div>
                </div>

                <div className="flex gap-2 mt-4 pt-3 border-t border-slate-100">
                  <button
                    onClick={() => handleApprove(order.id)}
                    disabled={isApproving || isRejecting}
                    className="flex-1 py-2.5 rounded-xl text-xs font-black bg-emerald-600 text-white shadow-sm hover:brightness-105 active:scale-[0.98] transition-all disabled:opacity-50"
                  >
                    {isApproving ? 'در حال تایید...' : 'تایید سفارش'}
                  </button>
                  <button
                    onClick={() => handleReject(order.id)}
                    disabled={isApproving || isRejecting}
                    className="py-2.5 px-4 rounded-xl text-xs font-bold border border-red-200 text-red-600 hover:bg-red-50 active:scale-[0.98] transition-all disabled:opacity-50"
                  >
                    {isRejecting ? '...' : 'رد سفارش'}
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── Active / Approved Orders Section (آماده دریافت) ── */}
      {activeOrders.length > 0 && (
        <div className="space-y-3">
          <p className="text-xs font-bold text-emerald-600 uppercase tracking-wide">📦 آماده دریافت ({activeOrders.length})</p>
          <div className="space-y-3">
            {activeOrders.map(order => (
              <div key={order.id} className="bg-white rounded-3xl p-5 shadow-sm border border-emerald-100 relative overflow-hidden">
                <div className="absolute top-0 right-0 left-0 h-1.5 bg-emerald-500" />
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-black text-slate-800">سفارش #{order.id}</span>
                      <span className="text-[10px] bg-emerald-50 text-emerald-700 border border-emerald-100 px-2 py-0.5 rounded-full font-bold">تایید شده</span>
                    </div>
                    <p className="text-xs text-slate-500 mt-2 font-semibold">
                      👤 خریدار: {order.customer_details?.first_name || order.customer_details?.last_name
                        ? `${order.customer_details.first_name || ''} ${order.customer_details.last_name || ''}`.trim()
                        : 'کاربر برکت'} ({order.customer_details?.phone_number || `شناسه: ${order.customer}`})
                    </p>
                    <p className="text-xs text-slate-400 mt-1">تعداد کیسه: {order.quantity}</p>
                  </div>
                  <div className="text-left">
                    <p className="text-sm font-black text-emerald-600">{parseFloat(order.total_price).toLocaleString()} ﷼</p>
                    <p className="text-[10px] text-slate-400 mt-1">
                      {new Date(order.created_at).toLocaleTimeString('fa-IR', { hour: '2-digit', minute: '2-digit' })}
                    </p>
                  </div>
                </div>
                <div className="bg-emerald-50/50 rounded-2xl p-3 text-center border border-emerald-100/50">
                  <p className="text-[10px] text-emerald-600 font-semibold mb-0.5">کد تحویل خریدار</p>
                  <p className="text-lg font-black tracking-widest text-emerald-800">{order.pickup_code}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── History Section ── */}
      {historyOrders.length > 0 && (
        <div className="space-y-2">
          <p className="text-xs font-bold text-slate-500 uppercase tracking-wide">🏁 تاریخچه سفارش‌ها</p>
          <div className="space-y-2">
            {historyOrders.map(order => {
              const isPickedUp = order.status === 'PICKED_UP';
              return (
                <div key={order.id} className="bg-white rounded-2xl p-4 shadow-sm border border-slate-100 flex items-center justify-between text-xs">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-black text-slate-700">سفارش #{order.id}</span>
                      <span className={`text-[9px] font-bold px-2 py-0.5 rounded-full ${isPickedUp ? 'bg-slate-100 text-slate-500' : 'bg-red-50 text-red-600 border border-red-100'
                        }`}>
                        {isPickedUp ? 'تحویل داده شده' : 'لغو شده'}
                      </span>
                    </div>
                    <p className="text-slate-400 mt-1">
                      خریدار: {order.customer_details?.phone_number || `شناسه: ${order.customer}`} • {order.quantity} کیسه
                    </p>
                  </div>
                  <div className="text-left">
                    <p className="font-bold text-slate-700">{parseFloat(order.total_price).toLocaleString()} ﷼</p>
                    <p className="text-[9px] text-slate-400 mt-0.5">
                      {new Date(order.created_at).toLocaleDateString('fa-IR')}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {ordersList.length === 0 && (
        <div className="bg-white rounded-3xl p-10 text-center shadow-sm border border-slate-100">
          <span className="text-5xl block mb-3">📦</span>
          <h3 className="font-black text-slate-700">سفارشی ثبت نشده</h3>
        </div>
      )}
    </div>
  );
};

// ─────────────────────────────────────────────
// PROFILE PAGE
// ─────────────────────────────────────────────
const ProfilePage = () => {
  const dispatch = useDispatch();
  const { userInfo } = useSelector((state: RootState) => state.auth);
  const { data: store, isLoading: storeLoading } = useGetMyStoreQuery();
  const navigate = useNavigate();

  const [apiData, setApiData] = useState<any>(null);
  useEffect(() => {
    api.get('users/profile/').then(r => {
      setApiData(r.data);
      dispatch(setUser(r.data));
    }).catch(() => { });
  }, [dispatch]);

  const displayUser = apiData || userInfo;
  const hasStore = !!store;
  const isAdmin = displayUser?.role === 'ADMIN';

  return (
    <div className="space-y-5">
      {/* User card */}
      <div className="bg-gradient-to-br from-emerald-600 to-green-500 rounded-3xl p-6 text-white shadow-xl shadow-emerald-500/20">
        <div className="flex items-center gap-4">
          <div className="w-16 h-16 rounded-2xl bg-white/20 flex items-center justify-center text-3xl font-black backdrop-blur-sm">
            {displayUser?.first_name ? displayUser.first_name[0].toUpperCase() : '👤'}
          </div>
          <div>
            <h2 className="text-xl font-black">
              {displayUser?.first_name && displayUser?.last_name
                ? `${displayUser.first_name} ${displayUser.last_name}`
                : 'کاربر برکت'}
            </h2>
            <p className="text-emerald-100 text-sm mt-0.5">{displayUser?.phone_number}</p>
            <div className="flex gap-2 mt-2 flex-wrap">
              <span className="text-xs bg-white/20 text-white px-2.5 py-0.5 rounded-full font-bold backdrop-blur-sm">خریدار</span>
              {hasStore && <span className="text-xs bg-white/20 text-white px-2.5 py-0.5 rounded-full font-bold backdrop-blur-sm">فروشنده</span>}
              {isAdmin && (
                <span className="text-xs bg-white/20 text-white px-2.5 py-0.5 rounded-full font-bold backdrop-blur-sm">
                  {displayUser?.is_super_admin ? 'مدیر اصلی' : 'مدیر'}
                </span>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Admin panel entry — only for ADMIN / super admin */}
      {isAdmin && (
        <div className="bg-white rounded-2xl p-4 shadow-sm border border-slate-200">
          <div className="flex items-center justify-between gap-3">
            <div className="flex items-center gap-3 min-w-0">
              <div className="w-11 h-11 rounded-xl bg-slate-900 flex items-center justify-center text-xl shrink-0">🛡️</div>
              <div className="min-w-0">
                <p className="font-black text-slate-800">پنل مدیریت</p>
                <p className="text-[11px] text-slate-400 font-semibold mt-0.5">
                  {displayUser?.is_super_admin
                    ? 'تایید محصولات و مدیریت ادمین‌ها'
                    : 'تایید محصولات و دسترسی‌های مدیریتی'}
                </p>
              </div>
            </div>
            <button
              onClick={() => navigate('/admin/panel')}
              className="shrink-0 px-4 py-2 rounded-xl text-xs font-black bg-slate-900 text-white hover:bg-slate-800 transition"
            >
              ورود →
            </button>
          </div>
        </div>
      )}

      {/* Shop section */}
      {storeLoading ? null : hasStore ? (
        <div className="bg-white rounded-2xl p-4 shadow-sm border border-slate-100">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-11 h-11 rounded-xl bg-emerald-50 flex items-center justify-center text-xl">🏪</div>
              <div>
                <p className="font-black text-slate-800">{store.name}</p>
                <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${store.status === 'APPROVED' ? 'bg-emerald-50 text-emerald-600' :
                  store.status === 'REJECTED' ? 'bg-red-50 text-red-600' : 'bg-amber-50 text-amber-600'
                  }`}>
                  {store.status === 'APPROVED' ? '✔️ تایید شده' : store.status === 'REJECTED' ? '❌ رد شده' : '⏳ در انتظار'}
                </span>
              </div>
            </div>
            <button onClick={() => navigate('/app/shop')}
              className="px-4 py-2 rounded-xl text-xs font-black bg-emerald-50 text-emerald-700 hover:bg-emerald-100 transition border border-emerald-100">
              مدیریت →
            </button>
          </div>
        </div>
      ) : (
        <div className="bg-white rounded-2xl p-5 shadow-sm border border-slate-100 text-center">
          <span className="text-4xl block mb-2">🏪</span>
          <h3 className="font-black text-slate-700 mb-1">فروشگاه خود را بسازید</h3>
          <p className="text-xs text-slate-400 mb-4">هم خریدار باشید هم فروشنده</p>
          <button onClick={() => navigate('/app/shop')}
            className="px-6 py-2.5 rounded-xl font-black text-sm bg-gradient-to-r from-emerald-600 to-green-500 text-white shadow-md shadow-emerald-500/20 hover:brightness-105 transition">
            ➕ ایجاد فروشگاه
          </button>
        </div>
      )}

      {/* Info card */}
      <div className="bg-white rounded-2xl p-5 shadow-sm border border-slate-100 space-y-3">
        <h3 className="font-black text-slate-700">اطلاعات حساب</h3>
        {[
          { label: 'شماره موبایل', value: displayUser?.phone_number || '—' },
          { label: 'نام', value: displayUser?.first_name || 'وارد نشده' },
          { label: 'نام خانوادگی', value: displayUser?.last_name || 'وارد نشده' },
        ].map(item => (
          <div key={item.label} className="flex items-center justify-between py-2 border-b border-slate-50 last:border-0">
            <span className="text-xs text-slate-400 font-semibold">{item.label}</span>
            <span className="text-sm font-bold text-slate-700">{item.value}</span>
          </div>
        ))}
      </div>

      {/* Logout */}
      <button
        onClick={() => dispatch(logout())}
        className="w-full py-4 rounded-2xl font-black text-red-500 bg-red-50 border border-red-100 hover:bg-red-100 transition"
      >
        🚪 خروج از حساب
      </button>
    </div>
  );
};

// ─────────────────────────────────────────────
// SHOP CREATE/REDIRECT for users without store
// ─────────────────────────────────────────────
const ShopOrCreate = () => {
  const { isLoading } = useGetMyStoreQuery();
  if (isLoading) return <div className="flex justify-center items-center h-64"><div className="w-10 h-10 rounded-full border-4 border-slate-200 border-t-emerald-500 animate-spin" /></div>;
  // Always show ShopPage — if no store, StoreProfilePage handles creation
  return <ShopPage />;
};

// ─────────────────────────────────────────────
// ADMIN PANEL PAGE
// ─────────────────────────────────────────────
type AdminBagFilter = 'PENDING' | 'APPROVED' | 'REJECTED' | 'ALL';
type AdminBagAction = 'approve' | 'reject' | 'reopen' | 'activate' | 'deactivate' | 'set_quantity';

const ADMIN_STATUS_META: Record<'PENDING' | 'APPROVED' | 'REJECTED', { label: string; className: string }> = {
  PENDING: { label: 'در انتظار', className: 'bg-amber-50 text-amber-700 border-amber-100' },
  APPROVED: { label: 'تایید شده', className: 'bg-emerald-50 text-emerald-700 border-emerald-100' },
  REJECTED: { label: 'رد شده', className: 'bg-red-50 text-red-700 border-red-100' },
};

const AdminProductsSection = () => {
  const [filter, setFilter] = useState<AdminBagFilter>('PENDING');
  const { data: bags, isLoading, isFetching } = useGetAdminBagsQuery(filter);
  const [approveRejectBag, { isLoading: isActioning }] = useApproveRejectBagMutation();
  const [zoomedImage, setZoomedImage] = useState<string | null>(null);
  const [editingQtyId, setEditingQtyId] = useState<number | null>(null);
  const [qtyDraft, setQtyDraft] = useState('');

  const handleAction = async (id: number, action: AdminBagAction, quantity?: number) => {
    try {
      await approveRejectBag({ id, action, quantity }).unwrap();
      setEditingQtyId(null);
    } catch (err: any) {
      alert('خطا در انجام عملیات: ' + (err.data?.detail || 'خطای سرور'));
    }
  };

  const startEditQty = (bag: { id: number; quantity: number }) => {
    setEditingQtyId(bag.id);
    setQtyDraft(String(bag.quantity));
  };

  const saveQty = (id: number) => {
    const quantity = parseInt(qtyDraft, 10);
    if (Number.isNaN(quantity) || quantity < 0) {
      alert('تعداد نامعتبر است.');
      return;
    }
    handleAction(id, 'set_quantity', quantity);
  };

  const tabs: { key: AdminBagFilter; label: string }[] = [
    { key: 'PENDING', label: 'در انتظار' },
    { key: 'APPROVED', label: 'تایید شده' },
    { key: 'REJECTED', label: 'رد شده' },
    { key: 'ALL', label: 'همه' },
  ];

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center h-64 gap-3">
        <div className="w-10 h-10 rounded-full border-4 border-slate-200 border-t-emerald-500 animate-spin" />
        <span className="text-sm text-slate-500 font-semibold">در حال دریافت محصولات...</span>
      </div>
    );
  }

  const bagsList = bags || [];
  const emptyCopy: Record<AdminBagFilter, { title: string; body: string }> = {
    PENDING: { title: 'صف بررسی خالی است', body: 'هیچ محصول جدیدی در انتظار تایید نیست.' },
    APPROVED: { title: 'محصول تاییدشده‌ای نیست', body: 'هنوز محصولی تایید و منتشر نشده است.' },
    REJECTED: { title: 'محصول ردی ثبت نشده', body: 'هیچ محصولی رد نشده است.' },
    ALL: { title: 'هنوز محصولی ثبت نشده', body: 'وقتی فروشندگان محصول بگذارند، اینجا نمایش داده می‌شود.' },
  };

  return (
    <div className="space-y-6" dir="rtl">
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <h1 className="text-xl font-black text-slate-800">🛡️ مدیریت محصولات</h1>
        <span className="text-xs bg-slate-100 text-slate-600 px-3 py-1.5 rounded-full border border-slate-200 font-bold">
          {bagsList.length} مورد {isFetching ? '• در حال بروزرسانی…' : ''}
        </span>
      </div>

      <div className="flex gap-2 overflow-x-auto pb-1">
        {tabs.map(tab => (
          <button
            key={tab.key}
            onClick={() => setFilter(tab.key)}
            className={`shrink-0 px-4 py-2 rounded-xl text-xs font-black border transition ${
              filter === tab.key
                ? 'bg-slate-900 text-white border-slate-900'
                : 'bg-white text-slate-500 border-slate-200 hover:bg-slate-50'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {bagsList.length === 0 ? (
        <div className="bg-white rounded-3xl p-12 text-center shadow-sm border border-slate-100">
          <span className="text-5xl block mb-3">📦</span>
          <h3 className="font-black text-slate-700">{emptyCopy[filter].title}</h3>
          <p className="text-xs text-slate-400 mt-1">{emptyCopy[filter].body}</p>
        </div>
      ) : (
        <div className="space-y-4">
          {bagsList.map(bag => {
            const status = bag.approval_status || 'PENDING';
            const statusMeta = ADMIN_STATUS_META[status];
            return (
              <div key={bag.id} className="bg-white rounded-3xl p-5 shadow-sm border border-slate-100 space-y-4">
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-center gap-3 min-w-0">
                    <div className="w-12 h-12 rounded-2xl bg-slate-50 flex items-center justify-center text-2xl shadow-inner flex-shrink-0">
                      {getCategoryEmoji(bag.category)}
                    </div>
                    <div className="min-w-0">
                      <h3 className="font-black text-slate-800 text-sm truncate">{bag.name}</h3>
                      <p className="text-xs text-slate-400 mt-0.5 font-semibold truncate">
                        {bag.store
                          ? `🏪 فروشگاه: ${bag.store.name}`
                          : `👤 فروشنده حقیقی: ${bag.seller_details?.first_name || bag.seller_details?.last_name
                            ? `${bag.seller_details.first_name || ''} ${bag.seller_details.last_name || ''}`.trim()
                            : 'کاربر برکت'}`}
                      </p>
                    </div>
                  </div>
                  <div className="flex flex-col items-end gap-1 shrink-0">
                    <span className={`text-[10px] font-bold px-2.5 py-1 rounded-md border ${statusMeta.className}`}>
                      {statusMeta.label}
                    </span>
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded-md ${
                      bag.is_active ? 'bg-emerald-50 text-emerald-600' : 'bg-slate-100 text-slate-500'
                    }`}>
                      {bag.is_active ? 'فعال در بازار' : 'غیرفعال'}
                    </span>
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-2 bg-slate-50 rounded-2xl p-3 text-xs">
                  <div>
                    <span className="text-[10px] text-slate-400 font-semibold block">قیمت اصلی</span>
                    <span className="font-bold text-slate-700 line-through">{parseFloat(bag.original_price).toLocaleString()} ﷼</span>
                  </div>
                  <div>
                    <span className="text-[10px] text-slate-400 font-semibold block">قیمت برکت</span>
                    <span className="font-black text-emerald-600">{parseFloat(bag.platform_price).toLocaleString()} ﷼</span>
                  </div>
                  <div>
                    <span className="text-[10px] text-slate-400 font-semibold block">موجودی / بازه</span>
                    <span className="font-black text-amber-600">{bag.quantity} عدد • {bag.pickup_start_time.slice(0, 5)}-{bag.pickup_end_time.slice(0, 5)}</span>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-1">
                    <span className="text-[10px] font-bold text-slate-400">🖼️ عکس محصول:</span>
                    <div className="relative h-28 rounded-2xl overflow-hidden border border-slate-100 bg-slate-50 cursor-zoom-in group"
                      onClick={() => setZoomedImage(getMediaUrl(bag.image as string))}>
                      {bag.image ? (
                        <img src={getMediaUrl(bag.image as string)} alt="Product" className="w-full h-full object-cover group-hover:scale-105 transition duration-300" />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center text-xs text-slate-400">بدون تصویر</div>
                      )}
                    </div>
                  </div>
                  <div className="space-y-1">
                    <span className="text-[10px] font-bold text-slate-400">🔍 برچسب انقضا / کیفیت:</span>
                    <div className="relative h-28 rounded-2xl overflow-hidden border border-slate-100 bg-slate-50 cursor-zoom-in group"
                      onClick={() => setZoomedImage(getMediaUrl(bag.expiry_image as string))}>
                      {bag.expiry_image ? (
                        <img src={getMediaUrl(bag.expiry_image as string)} alt="Expiry Label" className="w-full h-full object-cover group-hover:scale-105 transition duration-300" />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center text-xs text-slate-400">بدون تصویر</div>
                      )}
                    </div>
                  </div>
                </div>

                {/* Quantity editor */}
                <div className="flex items-center gap-2 flex-wrap bg-slate-50 rounded-2xl p-3">
                  <span className="text-[11px] font-bold text-slate-500">مدیریت موجودی:</span>
                  {editingQtyId === bag.id ? (
                    <>
                      <input
                        type="number"
                        min={0}
                        value={qtyDraft}
                        onChange={e => setQtyDraft(e.target.value)}
                        className="w-20 px-2 py-1.5 rounded-lg border border-slate-200 text-sm font-bold text-center"
                      />
                      <button
                        onClick={() => saveQty(bag.id)}
                        disabled={isActioning}
                        className="px-3 py-1.5 rounded-lg text-[11px] font-black bg-emerald-600 text-white disabled:opacity-50"
                      >
                        ذخیره
                      </button>
                      <button
                        onClick={() => setEditingQtyId(null)}
                        className="px-3 py-1.5 rounded-lg text-[11px] font-bold text-slate-500"
                      >
                        انصراف
                      </button>
                    </>
                  ) : (
                    <button
                      onClick={() => startEditQty(bag)}
                      className="px-3 py-1.5 rounded-lg text-[11px] font-black bg-white border border-slate-200 text-slate-700 hover:bg-slate-100"
                    >
                      تغییر تعداد ({bag.quantity})
                    </button>
                  )}
                </div>

                {/* Status / visibility actions */}
                <div className="flex flex-wrap gap-2 pt-2 border-t border-slate-50">
                  {status === 'PENDING' && (
                    <>
                      <button
                        onClick={() => handleAction(bag.id, 'approve')}
                        disabled={isActioning}
                        className="flex-1 min-w-[140px] py-3 rounded-xl font-black bg-emerald-600 text-white shadow-md shadow-emerald-500/20 hover:brightness-105 active:scale-[0.98] transition-all disabled:opacity-50 text-xs"
                      >
                        ✔️ تایید و انتشار
                      </button>
                      <button
                        onClick={() => handleAction(bag.id, 'reject')}
                        disabled={isActioning}
                        className="py-3 px-5 rounded-xl font-bold border border-red-200 text-red-600 hover:bg-red-50 active:scale-[0.98] transition-all disabled:opacity-50 text-xs"
                      >
                        ❌ رد
                      </button>
                    </>
                  )}

                  {status === 'APPROVED' && (
                    <>
                      {bag.is_active ? (
                        <button
                          onClick={() => handleAction(bag.id, 'deactivate')}
                          disabled={isActioning}
                          className="flex-1 min-w-[120px] py-3 rounded-xl font-black bg-slate-800 text-white hover:bg-slate-700 disabled:opacity-50 text-xs"
                        >
                          ⏸ غیرفعال کردن
                        </button>
                      ) : (
                        <button
                          onClick={() => handleAction(bag.id, 'activate')}
                          disabled={isActioning}
                          className="flex-1 min-w-[120px] py-3 rounded-xl font-black bg-emerald-600 text-white hover:brightness-105 disabled:opacity-50 text-xs"
                        >
                          ▶ فعال کردن
                        </button>
                      )}
                      <button
                        onClick={() => handleAction(bag.id, 'reject')}
                        disabled={isActioning}
                        className="py-3 px-4 rounded-xl font-bold border border-red-200 text-red-600 hover:bg-red-50 disabled:opacity-50 text-xs"
                      >
                        رد از بازار
                      </button>
                      <button
                        onClick={() => handleAction(bag.id, 'reopen')}
                        disabled={isActioning}
                        className="py-3 px-4 rounded-xl font-bold border border-amber-200 text-amber-700 hover:bg-amber-50 disabled:opacity-50 text-xs"
                      >
                        بازگشت به بررسی
                      </button>
                    </>
                  )}

                  {status === 'REJECTED' && (
                    <>
                      <button
                        onClick={() => handleAction(bag.id, 'approve')}
                        disabled={isActioning}
                        className="flex-1 min-w-[140px] py-3 rounded-xl font-black bg-emerald-600 text-white shadow-md shadow-emerald-500/20 hover:brightness-105 disabled:opacity-50 text-xs"
                      >
                        ✔️ تایید مجدد
                      </button>
                      <button
                        onClick={() => handleAction(bag.id, 'reopen')}
                        disabled={isActioning}
                        className="py-3 px-5 rounded-xl font-bold border border-amber-200 text-amber-700 hover:bg-amber-50 disabled:opacity-50 text-xs"
                      >
                        بازگشت به صف
                      </button>
                    </>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {zoomedImage && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/85 p-4" onClick={() => setZoomedImage(null)}>
          <div className="relative max-w-lg max-h-[80vh] bg-white rounded-3xl overflow-hidden shadow-2xl p-2" onClick={e => e.stopPropagation()}>
            <button className="absolute top-4 right-4 w-9 h-9 rounded-full bg-black/60 text-white font-bold flex items-center justify-center z-10" onClick={() => setZoomedImage(null)}>✕</button>
            <img src={zoomedImage} alt="Zoomed View" className="max-w-full max-h-[75vh] object-contain rounded-2xl" />
          </div>
        </div>
      )}
    </div>
  );
};

// Admin panel — products approval only (guarded by permission)
const AdminPanelPage = () => {
  const { userInfo } = useSelector((state: RootState) => state.auth);
  const canApprove = userInfo?.is_super_admin || userInfo?.admin_permissions?.includes('approve_products');

  if (!canApprove) {
    return (
      <div className="bg-white rounded-3xl p-12 text-center shadow-sm border border-slate-100" dir="rtl">
        <span className="text-5xl block mb-3">🔒</span>
        <h3 className="font-black text-slate-700">دسترسی محدود</h3>
        <p className="text-xs text-slate-400 mt-1">شما مجوز «تایید محصولات» را ندارید. با مدیر اصلی تماس بگیرید.</p>
      </div>
    );
  }

  return <AdminProductsSection />;
};

// ─────────────────────────────────────────────
// ADMIN AUTH: separate username/password login
// ─────────────────────────────────────────────
const AdminLogin = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const { userInfo } = useSelector((state: RootState) => state.auth);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [adminLogin, { isLoading }] = useAdminLoginMutation();

  useEffect(() => {
    if (userInfo?.role === 'ADMIN') navigate('/admin/panel', { replace: true });
  }, [userInfo, navigate]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    try {
      const res = await adminLogin({ username, password }).unwrap();
      dispatch(setCredentials({ accessToken: res.access, refreshToken: res.refresh, user: res.user }));
      navigate('/admin/panel', { replace: true });
    } catch (err: any) {
      setError(err.data?.error || 'نام کاربری یا رمز عبور نادرست است.');
    }
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-4 bg-gradient-to-b from-slate-900 via-slate-800 to-slate-900" dir="rtl">
      <div className="w-full max-w-sm z-10">
        <div className="text-center mb-6">
          <div className="w-16 h-16 mx-auto rounded-2xl bg-emerald-600 flex items-center justify-center text-3xl shadow-lg shadow-emerald-500/30 mb-3">🛡️</div>
          <h1 className="text-3xl font-black text-white mb-1">پنل مدیریت برکت</h1>
          <p className="text-slate-400 text-sm">ورود مدیران با نام کاربری و رمز عبور</p>
        </div>
        <div className="bg-white rounded-3xl shadow-2xl p-6 border border-slate-200">
          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <div className="p-3 rounded-xl bg-red-50 border border-red-200 text-red-600 text-sm font-medium text-center">
                {error}
              </div>
            )}
            <div>
              <label className="block text-xs font-bold text-slate-500 mb-1.5">نام کاربری</label>
              <input
                type="text"
                required
                value={username}
                onChange={e => setUsername(e.target.value)}
                placeholder="admin"
                className="w-full px-4 py-3 rounded-xl bg-slate-50 border border-slate-200 focus:outline-none focus:border-emerald-500 focus:bg-white text-sm transition"
              />
            </div>
            <div>
              <label className="block text-xs font-bold text-slate-500 mb-1.5">رمز عبور</label>
              <input
                type="password"
                required
                value={password}
                onChange={e => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full px-4 py-3 rounded-xl bg-slate-50 border border-slate-200 focus:outline-none focus:border-emerald-500 focus:bg-white text-sm transition"
              />
            </div>
            <button
              type="submit"
              disabled={isLoading || !username || !password}
              className="w-full py-3.5 rounded-xl font-black text-base bg-emerald-600 text-white shadow-lg shadow-emerald-500/30 hover:brightness-105 active:scale-[0.98] transition-all disabled:opacity-50"
            >
              {isLoading ? '⏳ در حال ورود...' : '🔐 ورود به پنل مدیریت'}
            </button>
          </form>
        </div>
        <p className="text-center text-xs text-slate-500 mt-6">
          این صفحه مخصوص مدیران است. کاربران عادی از <Link to="/login" className="text-emerald-400 font-bold">صفحه ورود کاربران</Link> استفاده کنند.
        </p>
      </div>
    </div>
  );
};

// Guards admin routes — must be authenticated with role ADMIN
const AdminProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const { isAuthenticated, userInfo } = useSelector((state: RootState) => state.auth);
  if (!isAuthenticated || userInfo?.role !== 'ADMIN') {
    return <Navigate to="/admin/login" replace />;
  }
  return <>{children}</>;
};

// Admin area layout with its own top bar + tabs (distinct from customer app)
const AdminLayout = () => {
  const { pathname } = useLocation();
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const { userInfo } = useSelector((state: RootState) => state.auth);

  const tabs = [
    { path: '/admin/panel', icon: '🎁', label: 'مدیریت محصولات' },
    ...(userInfo?.is_super_admin ? [{ path: '/admin/manage', icon: '👥', label: 'مدیریت ادمین‌ها' }] : []),
  ];

  const handleLogout = () => {
    dispatch(logout());
    navigate('/admin/login', { replace: true });
  };

  return (
    <div className="min-h-screen bg-slate-100 flex flex-col" dir="rtl">
      <header className="bg-slate-900 text-white sticky top-0 z-40 shadow-md">
        <div className="max-w-3xl mx-auto px-4 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-emerald-600 flex items-center justify-center text-xl">🛡️</div>
            <div>
              <span className="font-black text-lg block leading-tight">پنل مدیریت برکت</span>
              <span className="text-[10px] text-slate-400 font-semibold">
                {userInfo?.admin_username} {userInfo?.is_super_admin ? '• مدیر اصلی' : ''}
              </span>
            </div>
          </div>
          <button
            onClick={handleLogout}
            className="text-xs font-bold bg-red-500/20 text-red-300 px-3 py-2 rounded-lg hover:bg-red-500/30 transition"
          >
            🚪 خروج
          </button>
        </div>
        <div className="max-w-3xl mx-auto px-4 flex gap-1 pb-2">
          {tabs.map(t => {
            const isActive = pathname === t.path;
            return (
              <Link
                key={t.path}
                to={t.path}
                className={`px-4 py-2 rounded-lg text-xs font-black transition-all ${isActive ? 'bg-emerald-600 text-white' : 'text-slate-300 hover:bg-slate-800'}`}
              >
                {t.icon} {t.label}
              </Link>
            );
          })}
        </div>
      </header>
      <main className="flex-grow max-w-3xl mx-auto w-full px-4 py-5">
        <Outlet />
      </main>
    </div>
  );
};

// Super-admin: manage sub-admins (create / edit permissions / delete)
const AdminManagePage = () => {
  const { data: admins, isLoading } = useGetAdminsQuery();
  const { data: permData } = useGetAdminPermissionsQuery();
  const [createAdmin, { isLoading: isCreating }] = useCreateAdminMutation();
  const [updateAdmin] = useUpdateAdminMutation();
  const [deleteAdmin] = useDeleteAdminMutation();

  const availablePerms = permData?.permissions || ['approve_products'];

  const [showForm, setShowForm] = useState(false);
  const [newUsername, setNewUsername] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [newFirstName, setNewFirstName] = useState('');
  const [newPerms, setNewPerms] = useState<string[]>(['approve_products']);
  const [formError, setFormError] = useState('');
  const [successMsg, setSuccessMsg] = useState('');

  const togglePerm = (list: string[], perm: string) =>
    list.includes(perm) ? list.filter(p => p !== perm) : [...list, perm];

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(''); setSuccessMsg('');
    try {
      await createAdmin({
        admin_username: newUsername,
        password: newPassword,
        first_name: newFirstName,
        admin_permissions: newPerms,
      }).unwrap();
      setSuccessMsg(`ادمین «${newUsername}» ساخته شد ✅ — نام کاربری و رمز را به او بدهید.`);
      setNewUsername(''); setNewPassword(''); setNewFirstName(''); setNewPerms(['approve_products']);
      setShowForm(false);
    } catch (err: any) {
      const data = err.data;
      setFormError(data?.admin_username?.[0] || data?.password?.[0] || data?.error || 'خطا در ساخت ادمین.');
    }
  };

  const handleTogglePerm = async (admin: AdminUser, perm: string) => {
    const updated = togglePerm(admin.admin_permissions || [], perm);
    try {
      await updateAdmin({ phone_number: admin.phone_number, admin_permissions: updated }).unwrap();
    } catch { /* ignore */ }
  };

  const handleDelete = async (admin: AdminUser) => {
    if (!confirm(`حذف ادمین «${admin.admin_username}»؟`)) return;
    try {
      await deleteAdmin(admin.phone_number).unwrap();
    } catch (err: any) {
      alert(err.data?.error || 'خطا در حذف ادمین.');
    }
  };

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-40">
        <div className="w-10 h-10 rounded-full border-4 border-slate-200 border-t-emerald-500 animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-5" dir="rtl">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-black text-slate-800">👥 مدیریت ادمین‌ها</h1>
        <button
          onClick={() => { setShowForm(v => !v); setFormError(''); }}
          className="px-4 py-2 rounded-xl font-black text-sm bg-emerald-600 text-white shadow-md shadow-emerald-500/20 hover:brightness-105 transition"
        >
          {showForm ? '✕ بستن' : '➕ ادمین جدید'}
        </button>
      </div>

      {successMsg && <div className="p-3 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-700 text-xs font-bold">{successMsg}</div>}

      {/* Create form */}
      {showForm && (
        <form onSubmit={handleCreate} className="bg-white rounded-3xl p-5 shadow-sm border border-slate-100 space-y-4">
          <h3 className="font-black text-slate-700 text-sm">ساخت ادمین جدید</h3>
          {formError && <div className="p-3 rounded-xl bg-red-50 border border-red-200 text-red-600 text-xs font-bold">{formError}</div>}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-bold text-slate-500 mb-1.5">نام کاربری *</label>
              <input type="text" required value={newUsername} onChange={e => setNewUsername(e.target.value)}
                className="w-full px-3 py-3 rounded-xl bg-slate-50 border border-slate-200 focus:outline-none focus:border-emerald-500 text-sm transition" placeholder="admin2" />
            </div>
            <div>
              <label className="block text-xs font-bold text-slate-500 mb-1.5">رمز عبور *</label>
              <input type="text" required value={newPassword} onChange={e => setNewPassword(e.target.value)}
                className="w-full px-3 py-3 rounded-xl bg-slate-50 border border-slate-200 focus:outline-none focus:border-emerald-500 text-sm transition" placeholder="حداقل ۴ کاراکتر" />
            </div>
          </div>
          <div>
            <label className="block text-xs font-bold text-slate-500 mb-1.5">نام (اختیاری)</label>
            <input type="text" value={newFirstName} onChange={e => setNewFirstName(e.target.value)}
              className="w-full px-3 py-3 rounded-xl bg-slate-50 border border-slate-200 focus:outline-none focus:border-emerald-500 text-sm transition" placeholder="مثال: رضا" />
          </div>
          <div>
            <label className="block text-xs font-bold text-slate-500 mb-2">دسترسی‌ها</label>
            <div className="flex flex-wrap gap-2">
              {availablePerms.map(perm => {
                const active = newPerms.includes(perm);
                return (
                  <button type="button" key={perm} onClick={() => setNewPerms(p => togglePerm(p, perm))}
                    className={`px-3 py-2 rounded-xl text-xs font-black border transition ${active ? 'bg-emerald-600 text-white border-emerald-600' : 'bg-slate-50 text-slate-500 border-slate-200'}`}>
                    {active ? '✓ ' : ''}{PERMISSION_LABELS[perm] || perm}
                  </button>
                );
              })}
            </div>
          </div>
          <button type="submit" disabled={isCreating}
            className="w-full py-3.5 rounded-xl font-black bg-emerald-600 text-white shadow-md shadow-emerald-500/20 hover:brightness-105 active:scale-[0.98] transition-all disabled:opacity-50">
            {isCreating ? '⏳ در حال ساخت...' : '✅ ساخت ادمین'}
          </button>
        </form>
      )}

      {/* Admins list */}
      <div className="space-y-3">
        {(admins || []).map(admin => (
          <div key={admin.phone_number} className="bg-white rounded-2xl p-4 shadow-sm border border-slate-100">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-11 h-11 rounded-xl bg-slate-50 flex items-center justify-center text-xl">
                  {admin.is_super_admin ? '👑' : '👤'}
                </div>
                <div>
                  <p className="font-black text-slate-800 text-sm">
                    {admin.admin_username}
                    {admin.is_super_admin && <span className="mr-2 text-[10px] bg-amber-50 text-amber-700 border border-amber-100 px-2 py-0.5 rounded-full">مدیر اصلی</span>}
                  </p>
                  <p className="text-[11px] text-slate-400 mt-0.5">
                    {admin.first_name || '—'} {admin.last_name || ''}
                  </p>
                </div>
              </div>
              {!admin.is_super_admin && (
                <button onClick={() => handleDelete(admin)}
                  className="text-xs font-bold text-red-500 bg-red-50 px-3 py-1.5 rounded-lg hover:bg-red-100 transition">
                  🗑️ حذف
                </button>
              )}
            </div>
            {/* Permissions toggles */}
            <div className="mt-3 pt-3 border-t border-slate-50">
              <p className="text-[10px] font-bold text-slate-400 mb-2">دسترسی‌ها</p>
              {admin.is_super_admin ? (
                <span className="text-xs text-slate-500 font-semibold">دسترسی کامل (مدیر اصلی)</span>
              ) : (
                <div className="flex flex-wrap gap-2">
                  {availablePerms.map(perm => {
                    const active = (admin.admin_permissions || []).includes(perm);
                    return (
                      <button key={perm} onClick={() => handleTogglePerm(admin, perm)}
                        className={`px-3 py-1.5 rounded-lg text-[11px] font-black border transition ${active ? 'bg-emerald-600 text-white border-emerald-600' : 'bg-slate-50 text-slate-400 border-slate-200'}`}>
                        {active ? '✓ ' : ''}{PERMISSION_LABELS[perm] || perm}
                      </button>
                    );
                  })}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};


// ─────────────────────────────────────────────
// ROOT APP
// ─────────────────────────────────────────────
function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />

        {/* ── Admin area (separate username/password auth) ── */}
        <Route path="/admin/login" element={<AdminLogin />} />
        <Route
          element={
            <AdminProtectedRoute>
              <AdminLayout />
            </AdminProtectedRoute>
          }
        >
          <Route path="/admin/panel" element={<AdminPanelPage />} />
          <Route path="/admin/manage" element={<AdminManagePage />} />
          <Route path="/admin" element={<Navigate to="/admin/panel" replace />} />
        </Route>

        {/* Unified authenticated app */}
        <Route
          element={
            <ProtectedRoute>
              <AppLayout />
            </ProtectedRoute>
          }
        >
          <Route path="/app/discover" element={<DiscoveryPage />} />
          <Route path="/app/payment" element={<PaymentPage />} />
          <Route path="/app/orders" element={<MyOrdersPage />} />

          <Route path="/app/shop" element={<ShopOrCreate />} />
          <Route path="/app/profile" element={<ProfilePage />} />
          <Route index path="/app" element={<Navigate to="/app/discover" replace />} />
        </Route>


        {/* Legacy route redirects */}
        <Route path="/discovery" element={<Navigate to="/app/discover" replace />} />
        <Route path="/vendor/*" element={<Navigate to="/app/shop" replace />} />
        <Route path="/profile" element={<Navigate to="/app/profile" replace />} />
        <Route path="/my-orders" element={<Navigate to="/app/orders" replace />} />

        {/* Catch-all → if logged in go to app, else login */}
        <Route path="*" element={<Navigate to="/app/discover" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;

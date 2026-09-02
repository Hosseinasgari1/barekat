// Pure formatting/helper utilities shared across the app.

/**
 * Resolves a media path returned by the backend into an absolute URL.
 * Absolute URLs are returned untouched; relative paths are prefixed with the
 * backend origin derived from VITE_API_URL.
 */
export const getMediaUrl = (path: string | undefined | null): string => {
    if (!path) return '';
    if (path.startsWith('http://') || path.startsWith('https://')) return path;
    const apiURL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/';
    const backendBase = apiURL.replace(/\/api\/?$/, '');
    return `${backendBase}${path}`;
};

/** Formats a seconds count into a mm:ss string. */
export const formatCountdown = (totalSeconds: number): string => {
    const m = Math.floor(totalSeconds / 60).toString().padStart(2, '0');
    const s = (totalSeconds % 60).toString().padStart(2, '0');
    return `${m}:${s}`;
};

/** Formats a numeric/string price with thousands separators (fa-friendly). */
export const formatPrice = (value: string | number): string =>
    parseFloat(String(value)).toLocaleString();

/** Iranian mobile number validation (09xxxxxxxxx / +989xxxxxxxxx / 9xxxxxxxxx). */
export const isValidIranPhone = (phone: string): boolean =>
    /^(\+98|0)?9\d{9}$/.test(phone);

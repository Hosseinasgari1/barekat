// Product category configuration shared across the app.
// Single source of truth for category values, Persian labels, and emoji.

export interface CategoryOption {
    value: string;
    label: string;
}

export const categories: CategoryOption[] = [
    { value: 'VEGETABLES', label: '🍏 میوه و سبزیجات' },
    { value: 'SWEETS', label: '🍰 شیرینی و دسر' },
    { value: 'FOODS', label: '🍲 غذاهای آماده' },
    { value: 'SUPERMARKET', label: '🛒 سوپرمارکت' },
    { value: 'RESTAURANT', label: '🍔 رستوران و فست‌فود' },
    { value: 'BAKERY', label: '🍞 نان و نانوایی' },
    { value: 'BEVERAGES', label: '🥤 نوشیدنی‌ها' },
    { value: 'INGREDIENTS', label: '🌾 مواد اولیه' },
    { value: 'OTHER', label: '📦 سایر' },
];

const CATEGORY_EMOJI: Record<string, string> = {
    FOODS: '🍲',
    VEGETABLES: '🍏',
    SWEETS: '🍰',
    SUPERMARKET: '🛒',
    RESTAURANT: '🍔',
    BAKERY: '🍞',
    BEVERAGES: '🥤',
    INGREDIENTS: '🌾',
};

export const getCategoryEmoji = (cat?: string): string =>
    (cat && CATEGORY_EMOJI[cat]) || '📦';

/** Returns the short Persian label (without the leading emoji) for a category. */
export const getCategoryLabel = (cat?: string): string => {
    const found = categories.find((c) => c.value === cat);
    if (!found) return cat ?? '';
    return found.label.split(' ').slice(1).join(' ');
};

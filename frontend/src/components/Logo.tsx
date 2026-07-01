import React from 'react';

interface LogoProps {
  size?: 'sm' | 'md' | 'lg';
  showText?: boolean;
  className?: string;
}

const Logo: React.FC<LogoProps> = ({ size = 'md', showText = true, className = '' }) => {
  const sizes = {
    sm: { icon: 32, text: 'text-lg' },
    md: { icon: 40, text: 'text-xl' },
    lg: { icon: 48, text: 'text-2xl' },
  };

  const { icon, text } = sizes[size];

  return (
    <div className={`flex items-center gap-3 ${className}`}>
      {/* Icon */}
      <svg width={icon} height={icon} viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <linearGradient id="logo-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" style={{ stopColor: '#10b981' }} />
            <stop offset="100%" style={{ stopColor: '#059669' }} />
          </linearGradient>
        </defs>
        <circle cx="16" cy="16" r="15" fill="url(#logo-gradient)" />
        <text x="16" y="22" fontFamily="Vazirmatn, Arial, sans-serif" fontSize="18" fontWeight="700" fill="#ffffff" textAnchor="middle">
          ب
        </text>
      </svg>

      {/* Text */}
      {showText && (
        <span className={`font-bold text-brand-600 ${text}`} style={{ fontFamily: 'Vazirmatn, sans-serif' }}>
          برکت
        </span>
      )}
    </div>
  );
};

export default Logo;
// Card 원자 컴포넌트

import React from 'react';
import { classNames } from '../../../utils';

export interface CardProps {
  children: React.ReactNode;
  title?: string;
  subtitle?: string;
  headerAction?: React.ReactNode;
  footer?: React.ReactNode;
  padding?: 'none' | 'sm' | 'md' | 'lg';
  shadow?: 'none' | 'sm' | 'md' | 'lg';
  hover?: boolean;
  className?: string;
  onClick?: () => void;
}

const Card: React.FC<CardProps> = ({
  children,
  title,
  subtitle,
  headerAction,
  footer,
  padding = 'md',
  shadow = 'md',
  hover = false,
  className,
  onClick,
}) => {
  const baseStyles = 'bg-white rounded-lg border border-gray-200';
  
  const paddings = {
    none: '',
    sm: 'p-3',
    md: 'p-4',
    lg: 'p-6',
  };
  
  const shadows = {
    none: '',
    sm: 'shadow-sm',
    md: 'shadow-md',
    lg: 'shadow-lg',
  };
  
  const hoverStyles = hover ? 'transition-shadow hover:shadow-lg cursor-pointer' : '';
  
  return (
    <div
      className={classNames(
        baseStyles,
        shadows[shadow],
        hoverStyles,
        className
      )}
      onClick={onClick}
    >
      {(title || subtitle || headerAction) && (
        <div className={classNames('border-b border-gray-200', paddings[padding])}>
          <div className="flex items-center justify-between">
            <div>
              {title && (
                <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
              )}
              {subtitle && (
                <p className="mt-1 text-sm text-gray-500">{subtitle}</p>
              )}
            </div>
            {headerAction && <div>{headerAction}</div>}
          </div>
        </div>
      )}
      
      <div className={paddings[padding]}>
        {children}
      </div>
      
      {footer && (
        <div className={classNames('border-t border-gray-200 bg-gray-50', paddings[padding])}>
          {footer}
        </div>
      )}
    </div>
  );
};

export default Card;

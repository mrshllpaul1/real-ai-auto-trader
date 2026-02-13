/**
 * Enhanced Loading Skeletons
 * Reusable skeleton components for different data types
 */

import React from 'react';
import { motion } from 'framer-motion';

// Base skeleton with shimmer animation
const SkeletonBase = ({ className = '', animate = true }) => (
  <div
    className={`bg-[#1F1F1F] rounded ${animate ? 'animate-pulse' : ''} ${className}`}
  />
);

// Shimmer overlay for more realistic loading effect
const ShimmerOverlay = () => (
  <motion.div
    className="absolute inset-0 -translate-x-full bg-gradient-to-r from-transparent via-white/5 to-transparent"
    animate={{ translateX: ['100%', '-100%'] }}
    transition={{ duration: 1.5, repeat: Infinity, ease: 'linear' }}
  />
);

/**
 * Card Skeleton - For dashboard cards and stat boxes
 */
export const CardSkeleton = ({ count = 1, className = '' }) => (
  <div className={`grid gap-4 ${className}`}>
    {Array.from({ length: count }).map((_, i) => (
      <div
        key={i}
        className="bg-[#0A0A0A] border border-[#1F1F1F] rounded-xl p-4 relative overflow-hidden"
      >
        <div className="flex items-center gap-3 mb-3">
          <SkeletonBase className="w-10 h-10 rounded-lg" />
          <SkeletonBase className="h-4 w-24" />
        </div>
        <SkeletonBase className="h-8 w-32 mb-2" />
        <SkeletonBase className="h-4 w-20" />
        <ShimmerOverlay />
      </div>
    ))}
  </div>
);

/**
 * Stats Grid Skeleton - For stat card grids (2x2, 4x1, etc.)
 */
export const StatsGridSkeleton = ({ columns = 4 }) => (
  <div className={`grid grid-cols-2 lg:grid-cols-${columns} gap-4`}>
    {Array.from({ length: columns }).map((_, i) => (
      <div
        key={i}
        className="bg-gradient-to-br from-[#0A0A0A] to-[#111] border border-[#1F1F1F] rounded-xl p-4 relative overflow-hidden"
      >
        <div className="flex items-center gap-2 mb-2">
          <SkeletonBase className="w-5 h-5 rounded" />
          <SkeletonBase className="h-3 w-20" />
        </div>
        <SkeletonBase className="h-8 w-28 mb-1" />
        <SkeletonBase className="h-3 w-16" />
        <ShimmerOverlay />
      </div>
    ))}
  </div>
);

/**
 * Table Skeleton - For data tables
 */
export const TableSkeleton = ({ rows = 5, columns = 5 }) => (
  <div className="bg-[#0A0A0A] border border-[#1F1F1F] rounded-xl overflow-hidden">
    {/* Header */}
    <div className="bg-[#111] border-b border-[#1F1F1F] p-4 flex gap-4">
      {Array.from({ length: columns }).map((_, i) => (
        <SkeletonBase key={i} className="h-4 flex-1" />
      ))}
    </div>
    {/* Rows */}
    {Array.from({ length: rows }).map((_, rowIdx) => (
      <div
        key={rowIdx}
        className="p-4 border-b border-[#1F1F1F] last:border-0 flex gap-4 items-center relative overflow-hidden"
      >
        {Array.from({ length: columns }).map((_, colIdx) => (
          <SkeletonBase
            key={colIdx}
            className={`h-4 flex-1 ${colIdx === 0 ? 'max-w-[120px]' : ''}`}
          />
        ))}
        <ShimmerOverlay />
      </div>
    ))}
  </div>
);

/**
 * Chart Skeleton - For charts and graphs
 */
export const ChartSkeleton = ({ height = 300, type = 'line' }) => (
  <div
    className="bg-[#0A0A0A] border border-[#1F1F1F] rounded-xl p-4 relative overflow-hidden"
    style={{ height }}
  >
    <div className="flex justify-between items-center mb-4">
      <SkeletonBase className="h-5 w-32" />
      <div className="flex gap-2">
        <SkeletonBase className="h-6 w-12 rounded-full" />
        <SkeletonBase className="h-6 w-12 rounded-full" />
        <SkeletonBase className="h-6 w-12 rounded-full" />
      </div>
    </div>
    <div className="flex items-end justify-around h-[calc(100%-60px)] gap-2">
      {type === 'bar' ? (
        // Bar chart skeleton
        Array.from({ length: 12 }).map((_, i) => (
          <SkeletonBase
            key={i}
            className="flex-1 rounded-t"
            style={{ height: `${20 + Math.random() * 60}%` }}
          />
        ))
      ) : (
        // Line chart skeleton - curved line approximation
        <div className="w-full h-full flex items-center justify-center">
          <SkeletonBase className="w-full h-1/2 rounded-lg opacity-50" />
        </div>
      )}
    </div>
    <ShimmerOverlay />
  </div>
);

/**
 * Pie Chart Skeleton
 */
export const PieChartSkeleton = ({ size = 200 }) => (
  <div className="flex items-center justify-center gap-8">
    <div className="relative" style={{ width: size, height: size }}>
      <SkeletonBase className="w-full h-full rounded-full" />
      <div className="absolute inset-[30%] bg-[#0A0A0A] rounded-full" />
      <ShimmerOverlay />
    </div>
    <div className="space-y-3">
      {Array.from({ length: 5 }).map((_, i) => (
        <div key={i} className="flex items-center gap-2">
          <SkeletonBase className="w-3 h-3 rounded-full" />
          <SkeletonBase className="h-3 w-20" />
          <SkeletonBase className="h-3 w-12" />
        </div>
      ))}
    </div>
  </div>
);

/**
 * List Item Skeleton - For lists and feed items
 */
export const ListItemSkeleton = ({ count = 5, withAvatar = true }) => (
  <div className="space-y-3">
    {Array.from({ length: count }).map((_, i) => (
      <div
        key={i}
        className="bg-[#0A0A0A] border border-[#1F1F1F] rounded-xl p-4 flex items-center gap-4 relative overflow-hidden"
      >
        {withAvatar && <SkeletonBase className="w-12 h-12 rounded-full flex-shrink-0" />}
        <div className="flex-1 space-y-2">
          <SkeletonBase className="h-4 w-3/4" />
          <SkeletonBase className="h-3 w-1/2" />
        </div>
        <SkeletonBase className="h-8 w-20 rounded-lg" />
        <ShimmerOverlay />
      </div>
    ))}
  </div>
);

/**
 * Position Card Skeleton - For trading positions
 */
export const PositionSkeleton = ({ count = 3 }) => (
  <div className="space-y-4">
    {Array.from({ length: count }).map((_, i) => (
      <div
        key={i}
        className="bg-[#0A0A0A] border border-[#1F1F1F] rounded-xl p-4 relative overflow-hidden"
      >
        <div className="flex justify-between items-start mb-4">
          <div className="flex items-center gap-3">
            <SkeletonBase className="w-10 h-10 rounded-full" />
            <div>
              <SkeletonBase className="h-5 w-20 mb-1" />
              <SkeletonBase className="h-3 w-32" />
            </div>
          </div>
          <SkeletonBase className="h-6 w-16 rounded-full" />
        </div>
        <div className="grid grid-cols-4 gap-4">
          {Array.from({ length: 4 }).map((_, j) => (
            <div key={j}>
              <SkeletonBase className="h-3 w-16 mb-1" />
              <SkeletonBase className="h-5 w-20" />
            </div>
          ))}
        </div>
        <ShimmerOverlay />
      </div>
    ))}
  </div>
);

/**
 * AI Insight Skeleton - For AI recommendations
 */
export const AIInsightSkeleton = () => (
  <div className="bg-gradient-to-br from-[#9D00FF]/10 to-[#00FF94]/10 border border-[#9D00FF]/30 rounded-xl p-4 relative overflow-hidden">
    <div className="flex items-center gap-3 mb-4">
      <SkeletonBase className="w-8 h-8 rounded-lg" />
      <SkeletonBase className="h-5 w-40" />
      <SkeletonBase className="h-5 w-16 rounded-full ml-auto" />
    </div>
    <div className="space-y-2 mb-4">
      <SkeletonBase className="h-4 w-full" />
      <SkeletonBase className="h-4 w-5/6" />
      <SkeletonBase className="h-4 w-4/6" />
    </div>
    <div className="flex gap-2">
      <SkeletonBase className="h-9 w-24 rounded-lg" />
      <SkeletonBase className="h-9 w-24 rounded-lg" />
    </div>
    <ShimmerOverlay />
  </div>
);

/**
 * Form Skeleton - For forms and inputs
 */
export const FormSkeleton = ({ fields = 4 }) => (
  <div className="space-y-4">
    {Array.from({ length: fields }).map((_, i) => (
      <div key={i}>
        <SkeletonBase className="h-3 w-24 mb-2" />
        <SkeletonBase className="h-10 w-full rounded-lg" />
      </div>
    ))}
    <SkeletonBase className="h-10 w-32 rounded-lg mt-6" />
  </div>
);

/**
 * Trading Panel Skeleton
 */
export const TradingPanelSkeleton = () => (
  <div className="bg-[#0A0A0A] border border-[#1F1F1F] rounded-xl p-4 space-y-4 relative overflow-hidden">
    {/* Header */}
    <div className="flex justify-between items-center">
      <div className="flex gap-2">
        <SkeletonBase className="h-8 w-16 rounded-lg" />
        <SkeletonBase className="h-8 w-16 rounded-lg" />
      </div>
      <SkeletonBase className="h-6 w-24" />
    </div>
    
    {/* Price */}
    <div className="text-center py-4">
      <SkeletonBase className="h-10 w-40 mx-auto mb-2" />
      <SkeletonBase className="h-4 w-20 mx-auto" />
    </div>
    
    {/* Inputs */}
    <div className="space-y-3">
      <SkeletonBase className="h-12 w-full rounded-lg" />
      <SkeletonBase className="h-12 w-full rounded-lg" />
    </div>
    
    {/* Quick amounts */}
    <div className="flex gap-2">
      {[25, 50, 75, 100].map((_, i) => (
        <SkeletonBase key={i} className="h-8 flex-1 rounded-lg" />
      ))}
    </div>
    
    {/* Button */}
    <SkeletonBase className="h-12 w-full rounded-lg" />
    
    <ShimmerOverlay />
  </div>
);

/**
 * News Feed Skeleton
 */
export const NewsFeedSkeleton = ({ count = 4 }) => (
  <div className="space-y-4">
    {Array.from({ length: count }).map((_, i) => (
      <div
        key={i}
        className="bg-[#0A0A0A] border border-[#1F1F1F] rounded-xl p-4 relative overflow-hidden"
      >
        <div className="flex gap-4">
          <SkeletonBase className="w-24 h-24 rounded-lg flex-shrink-0" />
          <div className="flex-1 space-y-2">
            <SkeletonBase className="h-5 w-3/4" />
            <SkeletonBase className="h-4 w-full" />
            <SkeletonBase className="h-4 w-5/6" />
            <div className="flex gap-2 mt-2">
              <SkeletonBase className="h-5 w-16 rounded-full" />
              <SkeletonBase className="h-5 w-20 rounded-full" />
            </div>
          </div>
        </div>
        <ShimmerOverlay />
      </div>
    ))}
  </div>
);

/**
 * Full Page Skeleton - For entire page loading
 */
export const PageSkeleton = () => (
  <div className="min-h-screen bg-[#050505] p-4 lg:p-8 space-y-8">
    {/* Header */}
    <div className="flex justify-between items-center">
      <div className="flex items-center gap-4">
        <SkeletonBase className="w-12 h-12 rounded-xl" />
        <div>
          <SkeletonBase className="h-8 w-48 mb-2" />
          <SkeletonBase className="h-4 w-64" />
        </div>
      </div>
      <div className="flex gap-2">
        <SkeletonBase className="h-10 w-24 rounded-lg" />
        <SkeletonBase className="h-10 w-24 rounded-lg" />
      </div>
    </div>
    
    {/* Stats Grid */}
    <StatsGridSkeleton columns={4} />
    
    {/* Main Content */}
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <ChartSkeleton height={350} type="line" />
      <ChartSkeleton height={350} type="bar" />
    </div>
    
    {/* Table */}
    <TableSkeleton rows={5} columns={6} />
  </div>
);

/**
 * Dashboard Skeleton - For dashboard view
 */
export const DashboardSkeleton = () => (
  <div className="space-y-6">
    <StatsGridSkeleton columns={4} />
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <div className="lg:col-span-2">
        <ChartSkeleton height={300} />
      </div>
      <AIInsightSkeleton />
    </div>
    <PositionSkeleton count={3} />
  </div>
);

export default {
  CardSkeleton,
  StatsGridSkeleton,
  TableSkeleton,
  ChartSkeleton,
  PieChartSkeleton,
  ListItemSkeleton,
  PositionSkeleton,
  AIInsightSkeleton,
  FormSkeleton,
  TradingPanelSkeleton,
  NewsFeedSkeleton,
  PageSkeleton,
  DashboardSkeleton,
};

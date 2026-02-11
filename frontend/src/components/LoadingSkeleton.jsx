import React from 'react';
import { Loader2, Brain } from 'lucide-react';

/**
 * LoadingSkeleton - A beautiful loading component for page transitions
 * Shows an animated skeleton with the Tethys AI branding
 */
export const LoadingSkeleton = ({ message = "Loading..." }) => {
  return (
    <div className="min-h-screen bg-[#050505] flex items-center justify-center">
      <div className="flex flex-col items-center gap-4">
        {/* Animated Logo */}
        <div className="relative">
          <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-cyan-500 via-purple-500 to-pink-500 flex items-center justify-center animate-pulse">
            <Brain className="w-8 h-8 text-white" />
          </div>
          <div className="absolute -inset-1 rounded-2xl bg-gradient-to-br from-cyan-500/20 via-purple-500/20 to-pink-500/20 blur-lg animate-pulse" />
        </div>
        
        {/* Loading Text */}
        <div className="flex items-center gap-2 text-gray-400">
          <Loader2 className="w-4 h-4 animate-spin" />
          <span className="text-sm">{message}</span>
        </div>
        
        {/* Skeleton Cards */}
        <div className="flex gap-4 mt-4">
          <SkeletonCard />
          <SkeletonCard delay={100} />
          <SkeletonCard delay={200} />
        </div>
      </div>
    </div>
  );
};

/**
 * SkeletonCard - Individual animated skeleton card
 */
const SkeletonCard = ({ delay = 0 }) => (
  <div 
    className="w-32 h-24 rounded-xl bg-gray-900/50 border border-gray-800 p-3 animate-pulse"
    style={{ animationDelay: `${delay}ms` }}
  >
    <div className="w-8 h-8 rounded-lg bg-gray-800 mb-2" />
    <div className="w-full h-2 rounded bg-gray-800 mb-1" />
    <div className="w-2/3 h-2 rounded bg-gray-800" />
  </div>
);

/**
 * PageLoadingSkeleton - Full page loading skeleton with multiple sections
 */
export const PageLoadingSkeleton = () => {
  return (
    <div className="min-h-screen bg-[#050505] p-6">
      {/* Header Skeleton */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-gray-800 animate-pulse" />
          <div className="space-y-2">
            <div className="w-32 h-4 rounded bg-gray-800 animate-pulse" />
            <div className="w-24 h-3 rounded bg-gray-800 animate-pulse" />
          </div>
        </div>
        <div className="flex gap-2">
          <div className="w-24 h-9 rounded-lg bg-gray-800 animate-pulse" />
          <div className="w-24 h-9 rounded-lg bg-gray-800 animate-pulse" />
        </div>
      </div>
      
      {/* Stats Cards Skeleton */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="p-4 rounded-xl bg-gray-900/50 border border-gray-800 animate-pulse">
            <div className="flex items-center justify-between mb-3">
              <div className="w-8 h-8 rounded-lg bg-gray-800" />
              <div className="w-16 h-4 rounded bg-gray-800" />
            </div>
            <div className="w-24 h-6 rounded bg-gray-800 mb-1" />
            <div className="w-16 h-3 rounded bg-gray-800" />
          </div>
        ))}
      </div>
      
      {/* Main Content Skeleton */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 p-6 rounded-xl bg-gray-900/50 border border-gray-800 animate-pulse">
          <div className="w-40 h-5 rounded bg-gray-800 mb-4" />
          <div className="h-64 rounded-lg bg-gray-800/50" />
        </div>
        <div className="p-6 rounded-xl bg-gray-900/50 border border-gray-800 animate-pulse">
          <div className="w-32 h-5 rounded bg-gray-800 mb-4" />
          <div className="space-y-3">
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-full bg-gray-800" />
                <div className="flex-1 space-y-1">
                  <div className="w-20 h-3 rounded bg-gray-800" />
                  <div className="w-16 h-2 rounded bg-gray-800" />
                </div>
                <div className="w-12 h-4 rounded bg-gray-800" />
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

/**
 * CardSkeleton - Skeleton for individual card components
 */
export const CardSkeleton = ({ className = "" }) => (
  <div className={`p-4 rounded-xl bg-gray-900/50 border border-gray-800 animate-pulse ${className}`}>
    <div className="flex items-center gap-3 mb-3">
      <div className="w-10 h-10 rounded-lg bg-gray-800" />
      <div className="flex-1 space-y-2">
        <div className="w-24 h-4 rounded bg-gray-800" />
        <div className="w-16 h-3 rounded bg-gray-800" />
      </div>
    </div>
    <div className="space-y-2">
      <div className="w-full h-3 rounded bg-gray-800" />
      <div className="w-3/4 h-3 rounded bg-gray-800" />
    </div>
  </div>
);

/**
 * TableSkeleton - Skeleton for table loading
 */
export const TableSkeleton = ({ rows = 5 }) => (
  <div className="space-y-2 animate-pulse">
    {/* Header */}
    <div className="flex gap-4 p-3 border-b border-gray-800">
      <div className="w-20 h-4 rounded bg-gray-800" />
      <div className="w-24 h-4 rounded bg-gray-800" />
      <div className="w-16 h-4 rounded bg-gray-800" />
      <div className="w-20 h-4 rounded bg-gray-800" />
    </div>
    {/* Rows */}
    {Array(rows).fill(0).map((_, i) => (
      <div key={i} className="flex gap-4 p-3 items-center">
        <div className="w-8 h-8 rounded-full bg-gray-800" />
        <div className="w-20 h-4 rounded bg-gray-800" />
        <div className="w-24 h-4 rounded bg-gray-800" />
        <div className="w-16 h-4 rounded bg-gray-800" />
        <div className="w-20 h-4 rounded bg-gray-800" />
      </div>
    ))}
  </div>
);

export default LoadingSkeleton;

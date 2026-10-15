/**
 * Clip Assassin — Design Tokens
 * -----------------------------------------------------------------------
 * Single source of truth for colors, button variants, and card layout.
 * Import this into components instead of hardcoding hex/tailwind classes,
 * so every tool card stays visually consistent as the app grows.
 *
 * Usage:
 *   import { CATEGORY_COLORS, BUTTON_VARIANTS, CARD_STYLES } from './design-tokens';
 */

export type CategoryKey = 'magic' | 'organize' | 'destructive' | 'output' | 'render' | 'neutral';

// -----------------------------------------------------------------------
// 1. CATEGORY COLOR SYSTEM
// -----------------------------------------------------------------------
export const CATEGORY_COLORS: Record<CategoryKey, { name: string; solid: string; glow: string; text: string; examples?: string[] }> = {
  // Purple — AI / Magic / generative tools
  magic: {
    name: 'Magic',
    solid: '#A855F7',
    glow: 'rgba(168, 85, 247, 0.4)',
    text: '#C4B5FD',
    examples: ['Timeline Snapshot', 'Batch Clip Renamer', 'Quick Title', 'Quick Adjustment Layer'],
  },

  // Teal/Green — Organize, safe & reversible actions
  organize: {
    name: 'Organize',
    solid: '#10B981',
    glow: 'rgba(16, 185, 129, 0.4)',
    text: '#6EE7B7',
    examples: ['Magic Bin Organizer', 'Multi-Cam Auto Sync', 'Templates / Asset Library'],
  },

  // Red/Pink — Destructive or irreversible actions
  destructive: {
    name: 'Destructive',
    solid: '#F43F5E',
    glow: 'rgba(244, 63, 94, 0.4)',
    text: '#FDA4AF',
    examples: ['Silence Remover', 'Timecode Cutter', 'Clip Picker', 'BadWords Cleaner', 'Quick Cut & Ripple Delete'],
  },

  // Blue/Cyan — Export / Output actions
  output: {
    name: 'Output',
    solid: '#06B6D4',
    glow: 'rgba(6, 182, 212, 0.4)',
    text: '#67E8F9',
    examples: ['Multi-Cam Sync', 'Extract Thumbnails', 'Client Shotlist', 'Watermark Track'],
  },

  // Orange — Warnings / render-queue / merge-in-place actions
  render: {
    name: 'Render',
    solid: '#F97316',
    glow: 'rgba(249, 115, 22, 0.4)',
    text: '#FDBA74',
    examples: ['Multi-Platform Render', 'Merge Timelines', 'Auto YouTube Chapters'],
  },

  // Slate — Secondary/neutral actions
  neutral: {
    name: 'Neutral',
    solid: '#64748B',
    glow: 'rgba(100, 116, 139, 0.25)',
    text: '#CBD5E1',
    examples: ['Extract Flagged Clips', 'Extract Marked Clips', 'secondary/bulk actions'],
  },
};

// -----------------------------------------------------------------------
// 2. UNIFIED PRO BUTTON VARIANTS
// -----------------------------------------------------------------------
export const BUTTON_VARIANTS = {
  primary: (categoryKey: CategoryKey = 'magic') => {
    // Standardized minimal brand execution fill
    void categoryKey;
    const bg = 'var(--app-primary)';
    const glow = 'transparent';
    return {
      className: 'font-semibold rounded-lg px-5 py-3 text-xs transition-all duration-200 hover:brightness-110 active:scale-[0.98] flex items-center justify-center gap-2 shadow-lg cursor-pointer',
      style: {
        backgroundColor: bg,
        boxShadow: `0 0 20px ${glow}`,
        color: '#14121d',
      },
    };
  },

  secondary: {
    className: 'font-semibold rounded-lg px-5 py-3 text-xs transition-all duration-200 bg-white/10 hover:bg-white/15 active:scale-[0.98] border border-white/10 text-white/90 flex items-center justify-center gap-2 cursor-pointer',
    style: {},
  },
  
  destructive: {
    className: 'font-semibold rounded-lg px-5 py-3 text-xs transition-all duration-200 bg-rose-500/90 hover:bg-rose-500 active:scale-[0.98] text-white flex items-center justify-center gap-2 cursor-pointer shadow-lg shadow-rose-500/20',
    style: {},
  }
};

// -----------------------------------------------------------------------
// 3. CARD LAYOUT
// -----------------------------------------------------------------------
export const CARD_STYLES = {
  base: 'rounded-[24px] p-6 bg-[#191c23] border border-white/5 transition-all duration-300 ease-out hover:border-white/10 hover:bg-black/40 hover:-translate-y-1 hover:shadow-2xl flex flex-col relative group',
  minHeight: 'min-h-[180px]',
  gap: 'gap-6',
  iconWrapper: (categoryKey: CategoryKey) => ({
    className: 'w-10 h-10 rounded-lg flex items-center justify-center shrink-0',
    style: { backgroundColor: `${CATEGORY_COLORS[categoryKey].solid}22`, color: CATEGORY_COLORS[categoryKey].solid }, 
  }),
};

// -----------------------------------------------------------------------
// 4. INPUT FIELDS
// -----------------------------------------------------------------------
export const INPUT_STYLES = {
  base: 'w-full rounded-lg px-4 py-3 bg-[#13161d] border border-white/10 placeholder:text-gray-500 text-gray-100 transition-colors duration-150 focus:outline-none focus:border-opacity-100 focus:ring-1',
  focusRing: (categoryKey: CategoryKey) => ({
    '--tw-ring-color': CATEGORY_COLORS[categoryKey].solid,
  } as React.CSSProperties),
};

// -----------------------------------------------------------------------
// 5. SPACING SCALE
// -----------------------------------------------------------------------
export const SPACING = {
  cardInternalStack: 'space-y-4',
  inlineControlsGap: 'gap-3',
  sectionGap: 'space-y-6',
};

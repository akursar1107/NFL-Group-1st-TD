// Common styling constants for consistent UI across the app

export const colors = {
  // Primary colors
  primary: '#007bff',
  secondary: '#6c757d',
  success: '#28a745',
  danger: '#dc3545',
  warning: '#ffc107',
  info: '#17a2b8',
  
  // Grayscale
  white: '#fff',
  gray100: '#f8f9fa',
  gray200: '#e9ecef',
  gray300: '#dee2e6',
  gray400: '#ced4da',
  gray500: '#adb5bd',
  gray600: '#6c757d',
  gray700: '#495057',
  gray800: '#343a40',
  gray900: '#212529',
  black: '#000',
  
  // Text colors
  textPrimary: '#333',
  textSecondary: '#666',
  textMuted: '#999',
  
  // Background colors
  bgLight: '#f8f9fa',
  bgWhite: '#fff',
  
  // Border colors
  border: '#e0e0e0',
  borderLight: '#dee2e6',
  borderDark: '#ddd',
  
  // Position colors
  positionQB: '#007bff',
  positionRB: '#28a745',
  positionWR: '#ffc107',
  positionTE: '#17a2b8',
  positionOther: '#dc3545',
};

export const spacing = {
  xs: '4px',
  sm: '8px',
  md: '12px',
  lg: '16px',
  xl: '20px',
  xxl: '24px',
  xxxl: '32px',
};

export const borderRadius = {
  sm: '4px',
  md: '8px',
  lg: '12px',
};

export const fontSize = {
  xs: '12px',
  sm: '13px',
  base: '14px',
  md: '15px',
  lg: '16px',
  xl: '20px',
  xxl: '24px',
  xxxl: '32px',
  huge: '48px',
};

export const fontWeight = {
  normal: 'normal',
  medium: 600,
  bold: 'bold',
};

// Common component styles
export const modalStyles = {
  overlay: {
    position: 'fixed' as const,
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 1000,
  },
  container: {
    backgroundColor: colors.white,
    borderRadius: borderRadius.md,
    padding: '0',
    maxWidth: '800px',
    width: '90%',
    maxHeight: '90vh',
    overflow: 'auto',
    boxShadow: '0 4px 20px rgba(0, 0, 0, 0.15)',
    color: colors.textPrimary, // Override global dark theme
  },
  header: {
    padding: spacing.xxl,
    borderBottom: `1px solid ${colors.border}`,
    backgroundColor: colors.bgLight,
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    borderRadius: `${borderRadius.md} ${borderRadius.md} 0 0`,
  },
  headerTitle: {
    margin: 0,
    fontSize: fontSize.xl,
    color: `${colors.textPrimary} !important`, // Override global h2 styles
    fontWeight: fontWeight.medium,
  },
  closeButton: {
    background: 'none',
    border: 'none',
    fontSize: fontSize.xxxl,
    cursor: 'pointer',
    color: colors.textMuted,
    padding: '0',
    width: '32px',
    height: '32px',
    lineHeight: '24px',
    textAlign: 'center' as const,
    fontWeight: 300,
  },
  body: {
    padding: spacing.xxl,
    color: colors.textPrimary, // Override global dark theme
  },
};

export const tableStyles = {
  table: {
    width: '100%',
    borderCollapse: 'collapse' as const,
    marginBottom: spacing.xl,
    border: `1px solid ${colors.border}`,
  },
  thead: {
    backgroundColor: colors.bgLight,
    borderBottom: `1px solid ${colors.borderLight}`,
  },
  th: {
    padding: `${spacing.md} ${spacing.lg}`,
    textAlign: 'left' as const,
    fontWeight: fontWeight.medium,
    color: colors.textPrimary,
    fontSize: fontSize.sm,
    borderBottom: `1px solid ${colors.borderLight}`,
  },
  thCenter: {
    padding: `${spacing.md} ${spacing.lg}`,
    textAlign: 'center' as const,
    fontWeight: fontWeight.medium,
    color: colors.textPrimary,
    fontSize: fontSize.sm,
    borderBottom: `1px solid ${colors.borderLight}`,
  },
  thSortable: {
    padding: `${spacing.md} ${spacing.lg}`,
    textAlign: 'left' as const,
    borderBottom: `2px solid ${colors.borderDark}`,
    fontWeight: fontWeight.medium,
    color: colors.white,
    cursor: 'pointer',
    userSelect: 'none' as const,
  },
  thSortableCenter: {
    padding: `${spacing.md} ${spacing.lg}`,
    textAlign: 'center' as const,
    borderBottom: `2px solid ${colors.borderDark}`,
    fontWeight: fontWeight.medium,
    color: colors.white,
    cursor: 'pointer',
    userSelect: 'none' as const,
  },
  thDark: {
    padding: spacing.md,
    textAlign: 'left' as const,
    borderBottom: `2px solid ${colors.borderDark}`,
    fontWeight: fontWeight.medium,
    color: colors.white,
    backgroundColor: '#2c3e50',
  },
  td: {
    padding: `${spacing.md} ${spacing.lg}`,
    color: colors.textPrimary,
    fontSize: fontSize.base,
  },
  tdCenter: {
    padding: `${spacing.md} ${spacing.lg}`,
    textAlign: 'center' as const,
    color: colors.textPrimary,
    fontSize: fontSize.base,
  },
  tr: {
    borderBottom: `1px solid ${colors.border}`,
  },
  trStriped: (idx: number) => ({
    background: idx % 2 === 0 ? colors.white : colors.bgLight,
    transition: 'background-color 0.2s',
  }),
  trClickable: (idx: number) => ({
    background: idx % 2 === 0 ? colors.white : colors.bgLight,
    transition: 'background-color 0.2s',
    cursor: 'pointer',
  }),
};

export const badgeStyles = {
  base: {
    display: 'inline-block',
    padding: '4px 10px',
    borderRadius: borderRadius.sm,
    fontSize: fontSize.xs,
    fontWeight: fontWeight.medium,
    color: colors.white,
  },
  position: {
    display: 'inline-block',
    padding: '6px 14px',
    borderRadius: borderRadius.sm,
    color: colors.white,
    fontWeight: fontWeight.medium,
    fontSize: fontSize.sm,
    letterSpacing: '0.5px',
  },
  mainslate: {
    display: 'inline-block',
    padding: '4px 10px',
    borderRadius: borderRadius.sm,
    backgroundColor: colors.info,
    color: colors.white,
    fontSize: fontSize.xs,
    fontWeight: fontWeight.medium,
  },
};

export const cardStyles = {
  container: {
    padding: spacing.xxl,
    border: `1px solid ${colors.border}`,
    borderRadius: borderRadius.md,
    textAlign: 'center' as const,
    backgroundColor: colors.white,
  },
  label: {
    fontSize: fontSize.sm,
    color: colors.textSecondary,
    marginBottom: spacing.md,
    fontWeight: fontWeight.medium,
  },
  value: {
    fontSize: fontSize.huge,
    fontWeight: fontWeight.bold,
    color: colors.textPrimary,
  },
};

export const buttonStyles = {
  primary: {
    padding: `${spacing.md} ${spacing.xxl}`,
    backgroundColor: colors.primary,
    color: colors.white,
    border: 'none',
    borderRadius: borderRadius.sm,
    cursor: 'pointer',
    fontSize: fontSize.lg,
    fontWeight: fontWeight.medium,
  },
  secondary: {
    padding: `${spacing.md} ${spacing.xxl}`,
    backgroundColor: colors.secondary,
    color: colors.white,
    border: 'none',
    borderRadius: borderRadius.sm,
    cursor: 'pointer',
    fontSize: fontSize.lg,
    fontWeight: fontWeight.medium,
  },
};

// Helper functions
export function getPositionColor(position: string): string {
  if (!position) return colors.gray600;
  const pos = position.toUpperCase();
  
  if (pos === 'QB') return colors.positionQB;
  if (pos === 'RB') return colors.positionRB;
  if (pos === 'WR') return colors.positionWR;
  if (pos === 'TE') return colors.positionTE;
  
  return colors.positionOther;
}

export function getCellColor(rank: number): string {
  if (typeof rank !== 'number') return 'transparent';
  if (rank <= 10) return 'rgba(19, 176, 71, 0.2)';
  if (rank <= 22) return 'rgba(176, 150, 19, 0.2)';
  return 'rgba(180, 28, 43, 0.2)';
}

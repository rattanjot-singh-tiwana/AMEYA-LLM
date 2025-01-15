// types/email.ts

export interface EmailAccount {
  email: string;
  canDelete: boolean;
}

export interface EmailStats {
  total: number;
  read: number;
  unread: number;
  sent: number;
  drafted: number;
  avgResponse: string;
}

export interface SidebarProps {
  onAccountChange: (email: string | null) => void;
}

export interface DashboardProps {
  selectedAccount: string | null;
}
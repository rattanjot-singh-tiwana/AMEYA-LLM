"use client";

import React, { useState } from 'react';
import EmailSidebar from '@/components/email/sidebar';
import EmailDashboard from '@/components/email/dashboard';

const EmailMonitorLayout = () => {
  const [selectedAccount, setSelectedAccount] = useState<string | null>(null);

  const handleAccountChange = (email: string | null) => {
    setSelectedAccount(email);
  };

  return (
    <div className="flex h-screen bg-gray-50">
      <EmailSidebar onAccountChange={handleAccountChange} />
      <div className="flex-1 overflow-auto">
        <EmailDashboard selectedAccount={selectedAccount} />
      </div>
    </div>
  );
};

export default EmailMonitorLayout;
"use client";

import React, { useState, useEffect } from 'react';
import { Plus, Trash2, Mail } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { 
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogFooter,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { EmailAccount, SidebarProps } from '@/types/email';

// Add this function at the top of your sidebar.tsx file, after the imports

const fetchWithRetry = async (url: string, options: RequestInit = {}, retries = 3) => {
  for (let i = 0; i < retries; i++) {
    try {
      const response = await fetch(url, options);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      if (i === retries - 1) throw error; // Last retry
      await new Promise(resolve => setTimeout(resolve, 1000 * (i + 1))); // Exponential backoff
    }
  }
};

const EmailSidebar = ({ onAccountChange }: SidebarProps) => {
  const [accounts, setAccounts] = useState<EmailAccount[]>([]);
  const [newEmail, setNewEmail] = useState('');
  const [currentEmail, setCurrentEmail] = useState<string>('');
  const [selectedAccount, setSelectedAccount] = useState<string | null>(null);
  const [isOpen, setIsOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch current email on component mount
  useEffect(() => {
    const fetchCurrentEmail = async () => {
      try {
        const data = await fetchWithRetry('/api/health');
        if (data.currentEmail) {
          setCurrentEmail(data.currentEmail);
          // Set as selected account by default
          setSelectedAccount(data.currentEmail);
          if (onAccountChange) {
            onAccountChange(data.currentEmail);
          }
        }
      } catch (error) {
        console.error('Error fetching current email:', error);
        // Show error in UI
        setError('Failed to connect to email server. Please try again later.');
      }
    };
  
    fetchCurrentEmail();
  }, [onAccountChange]);

  const handleAddAccount = async () => {
    if (!newEmail || !newEmail.includes('@')) {
      setError('Please enter a valid email address');
      return;
    }

    try {
      setError(null);
      const response = await fetch('/api/set-email-service', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: newEmail }),
      });

      if (!response.ok) {
        throw new Error(`Failed to add account: ${response.statusText}`);
      }

      setAccounts([...accounts, { email: newEmail, canDelete: true }]);
      setNewEmail('');
      setIsOpen(false);
      handleAccountClick(newEmail); // Automatically switch to new account
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to add account');
      console.error('Error adding account:', err);
    }
  };

  const handleAccountClick = async (email: string) => {
    try {
      const response = await fetch('/api/set-email-service', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: email }),
      });

      if (!response.ok) {
        throw new Error('Failed to switch account');
      }

      setSelectedAccount(email);
      if (onAccountChange) {
        onAccountChange(email);
      }
    } catch (error) {
      console.error('Error switching account:', error);
    }
  };

  const handleDeleteAccount = async (emailToDelete: string) => {
    setAccounts(accounts.filter(account => account.email !== emailToDelete));
    if (selectedAccount === emailToDelete) {
      setSelectedAccount(null);
      if (onAccountChange) {
        onAccountChange(null);
      }
    }
  };

  return (
    <div className="w-64 bg-white h-screen border-r border-gray-200">
      <div className="flex items-center space-x-2 px-4 h-16 border-b border-gray-200">
        <Mail className="h-6 w-6 text-blue-500" />
        <span className="text-xl font-semibold text-gray-900">EmailMonitor</span>
      </div>
      
      <div className="p-4">
        <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-4">
          EMAIL ACCOUNTS
        </h2>
        
        <Dialog open={isOpen} onOpenChange={setIsOpen}>
          <DialogTrigger asChild>
            <Button 
              variant="secondary" 
              className="w-full flex items-center justify-center space-x-2 mb-4"
            >
              <Plus className="h-4 w-4" />
              <span>Add New Account</span>
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Add Email Account</DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              <div>
                <Label htmlFor="email">Email Address</Label>
                <Input 
                  id="email" 
                  type="email"
                  value={newEmail} 
                  onChange={(e) => setNewEmail(e.target.value)}
                  placeholder="Enter your email"
                  className="mt-1"
                />
                {error && <p className="text-sm text-red-500 mt-1">{error}</p>}
              </div>
            </div>
            <DialogFooter>
              <Button onClick={handleAddAccount} className="w-full">
                Add Account
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        <div className="space-y-2">
          {/* Current Email Account */}
          {currentEmail && (
            <div className="flex items-center space-x-2 p-2 bg-blue-50 rounded-md mb-2">
              <Mail className="h-4 w-4 text-blue-500" />
              <span className="text-sm text-gray-700 font-medium">{currentEmail}</span>
            </div>
          )}

          {accounts.map((account, index) => (
            account.email !== currentEmail && (
              <div 
                key={index}
                className={`flex items-center justify-between p-2 hover:bg-gray-50 rounded-md group cursor-pointer ${
                  selectedAccount === account.email ? 'bg-blue-50' : ''
                }`}
                onClick={() => handleAccountClick(account.email)}
              >
                <div className="flex items-center space-x-2">
                  <Mail className="h-4 w-4 text-gray-400" />
                  <span className="text-sm text-gray-700">{account.email}</span>
                </div>
                {account.canDelete && (
                  <Button 
                    variant="ghost" 
                    size="sm" 
                    className="opacity-0 group-hover:opacity-100"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDeleteAccount(account.email);
                    }}
                  >
                    <Trash2 className="h-4 w-4 text-gray-400 hover:text-red-500" />
                  </Button>
                )}
              </div>
            )
          ))}
        </div>
      </div>
    </div>
  );
};

export default EmailSidebar;
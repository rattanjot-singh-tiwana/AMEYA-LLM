"use client";

import React, { useState, useEffect } from 'react';
import { Mail, CheckCircle, AlertCircle, Send, MessageSquare, Clock } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import type { EmailStats, DashboardProps } from '@/types/email';
import TimeframeSelector from "@/components/ui/timeframe-selector";


const defaultStats: EmailStats = {
  total: 0,
  read: 0,
  unread: 0,
  sent: 0,
  drafted: 0,
  avgResponse: '0h',
};

const EmailDashboard: React.FC<DashboardProps> = ({ selectedAccount }) => {
  const [stats, setStats] = useState<EmailStats>(defaultStats);
  const [timeframe, setTimeframe] = useState<string>('24');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchEmailStats = async () => {
      try {
        setLoading(true);
        setError(null);
        
        const params = new URLSearchParams({
          hours: timeframe,
          ...(selectedAccount && { account: selectedAccount })
        });

        const response = await fetch(`/api/email-stats?${params}`);
        if (!response.ok) {
          throw new Error('Failed to fetch email stats');
        }
        
        const data = await response.json();
        setStats({
          total: data.total || 0,
          read: data.read || 0,
          unread: data.unread || 0,
          sent: data.sent || 0,
          drafted: data.drafted || 0,
          avgResponse: data.avgResponse || '0h'
        });
      } catch (err) {
        setError(err instanceof Error ? err.message : 'An error occurred');
        console.error('Error fetching email stats:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchEmailStats();
  }, [timeframe, selectedAccount]); // Refetch when account or timeframe changes

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="bg-red-50 text-red-500 p-4 rounded-md">
          Error: {error}
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-2xl font-semibold text-gray-900">Email Monitoring Dashboard</h1>
              <p className="mt-1 text-sm text-gray-600">
                {selectedAccount ? `Viewing: ${selectedAccount}` : 'Welcome back, Admin'}
              </p>
            </div>
            <TimeframeSelector onTimeframeChange={setTimeframe} />
          </div>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="max-w-7xl mx-auto px-4 py-6">
        <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-6">
          {/* Total Received */}
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Total Received</p>
                  <p className="mt-1 text-3xl font-semibold text-gray-900">{stats.total}</p>
                </div>
                <Mail className="h-8 w-8 text-blue-500" />
              </div>
            </CardContent>
          </Card>

          {/* Read */}
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Read</p>
                  <p className="mt-1 text-3xl font-semibold text-gray-900">{stats.read}</p>
                </div>
                <CheckCircle className="h-8 w-8 text-green-500" />
              </div>
            </CardContent>
          </Card>

          {/* Unread */}
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Unread</p>
                  <p className="mt-1 text-3xl font-semibold text-gray-900">{stats.unread}</p>
                </div>
                <AlertCircle className="h-8 w-8 text-red-500" />
              </div>
            </CardContent>
          </Card>

          {/* Sent */}
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Sent</p>
                  <p className="mt-1 text-3xl font-semibold text-gray-900">{stats.sent}</p>
                </div>
                <Send className="h-8 w-8 text-blue-500" />
              </div>
            </CardContent>
          </Card>

          {/* Drafted */}
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Drafted</p>
                  <p className="mt-1 text-3xl font-semibold text-gray-900">{stats.drafted}</p>
                </div>
                <MessageSquare className="h-8 w-8 text-purple-500" />
              </div>
            </CardContent>
          </Card>

          {/* Avg Response */}
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Avg Response</p>
                  <p className="mt-1 text-3xl font-semibold text-gray-900">{stats.avgResponse}</p>
                </div>
                <Clock className="h-8 w-8 text-orange-500" />
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default EmailDashboard;
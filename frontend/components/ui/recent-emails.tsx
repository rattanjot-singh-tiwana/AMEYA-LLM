import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Mail, Star, Clock, User } from 'lucide-react';

interface Email {
  id: string;
  subject: string;
  sender: string;
  timestamp: string;
  isRead: boolean;
  isStarred: boolean;
}

interface RecentEmailsProps {
  emails: Email[];
}

const RecentEmails = ({ emails }: RecentEmailsProps) => {
  return (
    <Card className="mt-8">
      <CardHeader>
        <CardTitle className="text-xl font-semibold">Recent Emails</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="divide-y divide-gray-100">
          {emails.map((email) => (
            <div
              key={email.id}
              className="py-4 flex items-center justify-between hover:bg-gray-50 cursor-pointer rounded-lg px-4"
            >
              <div className="flex items-center space-x-4">
                <div className={`p-2 rounded-full ${email.isRead ? 'bg-gray-100' : 'bg-blue-100'}`}>
                  <Mail 
                    className={`h-5 w-5 ${email.isRead ? 'text-gray-500' : 'text-blue-500'}`} 
                  />
                </div>
                <div>
                  <h3 className={`text-sm font-medium ${email.isRead ? 'text-gray-600' : 'text-gray-900'}`}>
                    {email.subject}
                  </h3>
                  <div className="flex items-center space-x-2 mt-1">
                    <User className="h-4 w-4 text-gray-400" />
                    <span className="text-xs text-gray-500">{email.sender}</span>
                  </div>
                </div>
              </div>
              <div className="flex items-center space-x-4">
                <Star 
                  className={`h-5 w-5 ${email.isStarred ? 'text-yellow-400 fill-yellow-400' : 'text-gray-300'}`} 
                />
                <div className="flex items-center text-xs text-gray-500">
                  <Clock className="h-4 w-4 mr-1" />
                  {email.timestamp}
                </div>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
};

export default RecentEmails;
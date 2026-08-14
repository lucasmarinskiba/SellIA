'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

export const RetentionPlaybookBuilder = ({ customerId }: { customerId: string }) => {
  return (
    <Card>
      <CardHeader>
        <CardTitle>📧 Retention Playbook Builder</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <p className="font-semibold text-sm">Generated Playbook:</p>
          <div className="bg-gray-50 p-4 rounded text-sm">
            <p className="font-semibold mb-2">Subject: "We've adjusted your pricing"</p>
            <p className="text-gray-700">Hi there,</p>
            <p className="text-gray-700 mt-2">We noticed your recent engagement has decreased. We'd love to help get you back on track.</p>
            <p className="text-gray-700 mt-2">💡 Special offer: 30% discount for 3 months + free training</p>
          </div>
        </div>
        <div className="flex gap-2">
          <Button variant="outline">Preview</Button>
          <Button className="bg-blue-600 hover:bg-blue-700">Send Campaign</Button>
        </div>
      </CardContent>
    </Card>
  );
};


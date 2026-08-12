'use client';

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';

interface SocialContentGeneratorProps {
  dealId: string;
  triggerType: string;
  companyName: string;
  industry: string;
}

export const SocialContentGenerator = ({
  dealId,
  triggerType,
  companyName,
  industry,
}: SocialContentGeneratorProps) => {
  const [selectedFormat, setSelectedFormat] = useState<'linkedin' | 'twitter' | 'email' | 'video'>('linkedin');
  const [content, setContent] = useState('');
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);

  const generateContent = async () => {
    setLoading(true);
    try {
      const endpoint =
        selectedFormat === 'email' ? '/api/v1/foom/email-subject' :
        selectedFormat === 'video' ? '/api/v1/foom/video-script' :
        '/api/v1/foom/social-post';

      const res = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          deal_id: dealId,
          trigger_type: triggerType,
          company_name: companyName,
          industry: industry,
          duration_seconds: selectedFormat === 'video' ? 30 : undefined,
        }),
      });

      const data = await res.json();
      setContent(
        selectedFormat === 'email' ? data.subject :
        selectedFormat === 'video' ? data.script :
        data.post
      );
    } catch (error) {
      console.error('Failed to generate content:', error);
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = () => {
    navigator.clipboard.writeText(content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle>📱 Generate Shareable Content</CardTitle>
        <p className="text-sm text-gray-600 mt-2">
          Create FOOM-triggering content your users can post to sell their products
        </p>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Format Selection */}
        <div>
          <p className="text-sm font-semibold text-gray-700 mb-3">Choose Format:</p>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
            {[
              { id: 'linkedin', label: 'LinkedIn', icon: '💼' },
              { id: 'twitter', label: 'Twitter', icon: '𝕏' },
              { id: 'email', label: 'Email', icon: '📧' },
              { id: 'video', label: 'Video', icon: '🎥' },
            ].map((fmt) => (
              <button
                key={fmt.id}
                onClick={() => {
                  setSelectedFormat(fmt.id as any);
                  setContent('');
                }}
                className={`p-3 rounded-lg border-2 transition ${
                  selectedFormat === fmt.id
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200 hover:border-blue-300'
                }`}
              >
                <p className="text-2xl mb-1">{fmt.icon}</p>
                <p className="text-xs font-semibold">{fmt.label}</p>
              </button>
            ))}
          </div>
        </div>

        {/* Generate Button */}
        <Button
          onClick={generateContent}
          disabled={loading}
          className="w-full bg-blue-600 hover:bg-blue-700"
          size="lg"
        >
          {loading ? 'Generating...' : `Generate ${selectedFormat === 'email' ? 'Subject' : selectedFormat === 'video' ? 'Script' : 'Post'}`}
        </Button>

        {/* Generated Content */}
        {content && (
          <div className="space-y-3">
            <div className="bg-gray-50 p-4 rounded-lg">
              <p className="text-xs font-semibold text-gray-700 mb-2">Generated Content:</p>
              <p className="text-sm text-gray-900 whitespace-pre-wrap">{content}</p>
            </div>

            <div className="flex gap-2">
              <Button
                onClick={copyToClipboard}
                variant="outline"
                className="flex-1"
              >
                {copied ? '✓ Copied!' : 'Copy to Clipboard'}
              </Button>
              <Button
                onClick={generateContent}
                disabled={loading}
                variant="outline"
                className="flex-1"
              >
                Regenerate
              </Button>
            </div>

            {/* Platform-specific tips */}
            <div className="bg-blue-50 border-l-4 border-blue-500 p-4 rounded">
              <p className="text-xs font-semibold text-blue-900 mb-2">
                {selectedFormat === 'linkedin' && '💡 LinkedIn Tips:'}
                {selectedFormat === 'twitter' && '💡 Twitter Tips:'}
                {selectedFormat === 'email' && '💡 Email Tips:'}
                {selectedFormat === 'video' && '💡 Video Tips:'}
              </p>
              <ul className="text-xs text-blue-800 space-y-1">
                {selectedFormat === 'linkedin' && (
                  <>
                    <li>✓ Post at 8-10am on Tuesday-Thursday</li>
                    <li>✓ Use line breaks for readability</li>
                    <li>✓ Include 3-5 relevant hashtags</li>
                    <li>✓ Add emoji to break up text</li>
                  </>
                )}
                {selectedFormat === 'twitter' && (
                  <>
                    <li>✓ Post multiple times for reach</li>
                    <li>✓ Thread format performs better</li>
                    <li>✓ Ask questions to boost engagement</li>
                    <li>✓ Reply to trending conversations</li>
                  </>
                )}
                {selectedFormat === 'email' && (
                  <>
                    <li>✓ Send Tuesday-Thursday 9-11am</li>
                    <li>✓ A/B test subject lines</li>
                    <li>✓ Personalize with [FirstName]</li>
                    <li>✓ Target 30-35% open rate baseline</li>
                  </>
                )}
                {selectedFormat === 'video' && (
                  <>
                    <li>✓ Hook in first 3 seconds</li>
                    <li>✓ Text overlay for sound-off viewing</li>
                    <li>✓ Post to TikTok, Instagram Reels, YouTube</li>
                    <li>✓ Vertical format (9:16)</li>
                  </>
                )}
              </ul>
            </div>
          </div>
        )}

        {/* How users benefit */}
        <Card className="bg-green-50 border-green-200">
          <CardContent className="pt-6">
            <p className="text-sm font-semibold text-green-900 mb-2">Why This Works for Users:</p>
            <p className="text-xs text-green-800">
              Users can post FOOM-ready content showing their prospects urgency, scarcity, and social proof. SellIA creates
              content for users → users sell better → users upgrade to paid → network effect.
            </p>
          </CardContent>
        </Card>
      </CardContent>
    </Card>
  );
};

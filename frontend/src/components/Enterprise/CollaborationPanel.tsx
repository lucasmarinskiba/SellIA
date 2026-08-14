'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { MessageSquare, CheckCircle2, Hand, Bell, Send } from 'lucide-react';

interface Comment {
  id: string;
  user_name: string;
  content: string;
  created_at: string;
}

interface Approval {
  id: string;
  action_type: string;
  requester_name: string;
  status: 'pending' | 'approved' | 'rejected';
  created_at: string;
}

interface Handoff {
  id: string;
  deal_id: string;
  from_user: string;
  reason: string;
  notes: string;
  created_at: string;
}

export const CollaborationPanel: React.FC<{ dealId: string; userId: string }> = ({ dealId, userId }) => {
  const [comments, setComments] = useState<Comment[]>([]);
  const [approvals, setApprovals] = useState<Approval[]>([]);
  const [handoffs, setHandoffs] = useState<Handoff[]>([]);
  const [newComment, setNewComment] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadCollaborationData();
  }, [dealId, userId]);

  const loadCollaborationData = async () => {
    try {
      setLoading(true);
      // Fetch comments
      const commentsRes = await fetch(`/api/v1/collaboration/deals/${dealId}/comments`);
      if (commentsRes.ok) {
        const data = await commentsRes.json();
        setComments(data.comments || []);
      }

      // Fetch pending approvals
      const approvalsRes = await fetch(`/api/v1/collaboration/approvals/pending/${userId}`);
      if (approvalsRes.ok) {
        const data = await approvalsRes.json();
        setApprovals(data.approvals || []);
      }

      // Fetch incoming handoffs
      const handoffsRes = await fetch(`/api/v1/collaboration/handoffs/incoming/${userId}`);
      if (handoffsRes.ok) {
        const data = await handoffsRes.json();
        setHandoffs(data.handoffs || []);
      }
    } catch (error) {
      console.error('Collaboration data load error:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAddComment = async () => {
    if (!newComment.trim()) return;

    try {
      const res = await fetch(`/api/v1/collaboration/deals/${dealId}/comments`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: userId,
          user_name: 'Current User',
          content: newComment,
        }),
      });

      if (res.ok) {
        setNewComment('');
        loadCollaborationData();
      }
    } catch (error) {
      console.error('Comment submit error:', error);
    }
  };

  const handleApprove = async (approvalId: string) => {
    try {
      await fetch(`/api/v1/collaboration/approvals/${approvalId}/decide`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          approver_id: userId,
          decision: 'approved',
        }),
      });
      loadCollaborationData();
    } catch (error) {
      console.error('Approval error:', error);
    }
  };

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Team Collaboration</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-12 bg-gray-200 rounded animate-pulse" />
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      <Tabs defaultValue="comments" className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="comments" className="flex items-center gap-2">
            <MessageSquare className="w-4 h-4" />
            Comments
            {comments.length > 0 && <Badge variant="secondary">{comments.length}</Badge>}
          </TabsTrigger>
          <TabsTrigger value="approvals" className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4" />
            Approvals
            {approvals.length > 0 && <Badge variant="secondary">{approvals.length}</Badge>}
          </TabsTrigger>
          <TabsTrigger value="handoffs" className="flex items-center gap-2">
            <Hand className="w-4 h-4" />
            Handoffs
            {handoffs.length > 0 && <Badge variant="secondary">{handoffs.length}</Badge>}
          </TabsTrigger>
        </TabsList>

        {/* Comments Tab */}
        <TabsContent value="comments">
          <Card>
            <CardHeader>
              <CardTitle>Deal Comments</CardTitle>
              <CardDescription>Real-time team discussion (internal only)</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Comment List */}
              <div className="space-y-3 max-h-96 overflow-y-auto">
                {comments.length === 0 ? (
                  <p className="text-sm text-gray-500">No comments yet</p>
                ) : (
                  comments.map((comment) => (
                    <div key={comment.id} className="p-3 bg-slate-50 border rounded-lg">
                      <div className="flex justify-between items-start">
                        <p className="font-semibold text-sm">{comment.user_name}</p>
                        <span className="text-xs text-gray-500">
                          {new Date(comment.created_at).toLocaleTimeString()}
                        </span>
                      </div>
                      <p className="text-sm text-slate-700 mt-1">{comment.content}</p>
                    </div>
                  ))
                )}
              </div>

              {/* Add Comment */}
              <div className="flex gap-2 mt-4">
                <input
                  type="text"
                  value={newComment}
                  onChange={(e) => setNewComment(e.target.value)}
                  placeholder="Add a comment..."
                  className="flex-1 px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  onKeyPress={(e) => e.key === 'Enter' && handleAddComment()}
                />
                <button
                  onClick={handleAddComment}
                  className="px-3 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 flex items-center gap-2"
                >
                  <Send className="w-4 h-4" />
                </button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Approvals Tab */}
        <TabsContent value="approvals">
          <Card>
            <CardHeader>
              <CardTitle>Pending Approvals</CardTitle>
              <CardDescription>Actions requiring your sign-off</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {approvals.length === 0 ? (
                <p className="text-sm text-gray-500">No pending approvals</p>
              ) : (
                approvals.map((approval) => (
                  <div key={approval.id} className="p-4 border rounded-lg">
                    <div className="flex justify-between items-start mb-2">
                      <div>
                        <p className="font-semibold text-sm">{approval.action_type}</p>
                        <p className="text-sm text-gray-600">Requested by {approval.requester_name}</p>
                      </div>
                      <Badge
                        variant={
                          approval.status === 'approved'
                            ? 'default'
                            : approval.status === 'rejected'
                              ? 'destructive'
                              : 'secondary'
                        }
                      >
                        {approval.status}
                      </Badge>
                    </div>
                    {approval.status === 'pending' && (
                      <div className="flex gap-2 mt-3">
                        <button
                          onClick={() => handleApprove(approval.id)}
                          className="flex-1 px-3 py-2 bg-green-500 text-white rounded text-sm hover:bg-green-600"
                        >
                          Approve
                        </button>
                        <button className="flex-1 px-3 py-2 bg-red-500 text-white rounded text-sm hover:bg-red-600">
                          Reject
                        </button>
                      </div>
                    )}
                  </div>
                ))
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Handoffs Tab */}
        <TabsContent value="handoffs">
          <Card>
            <CardHeader>
              <CardTitle>Incoming Handoffs</CardTitle>
              <CardDescription>Deals passed to you from teammates</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {handoffs.length === 0 ? (
                <p className="text-sm text-gray-500">No incoming handoffs</p>
              ) : (
                handoffs.map((handoff) => (
                  <div key={handoff.id} className="p-4 border rounded-lg">
                    <div className="mb-2">
                      <p className="font-semibold text-sm">Deal {handoff.deal_id}</p>
                      <p className="text-sm text-gray-600">From: {handoff.from_user}</p>
                    </div>
                    <p className="text-sm text-slate-700 mb-2">
                      <span className="font-medium">Reason:</span> {handoff.reason}
                    </p>
                    {handoff.notes && (
                      <p className="text-sm text-slate-600 mb-3">
                        <span className="font-medium">Notes:</span> {handoff.notes}
                      </p>
                    )}
                    <div className="flex gap-2">
                      <button className="flex-1 px-3 py-2 bg-green-500 text-white rounded text-sm hover:bg-green-600">
                        Accept
                      </button>
                      <button className="flex-1 px-3 py-2 bg-gray-300 text-gray-700 rounded text-sm hover:bg-gray-400">
                        Decline
                      </button>
                    </div>
                  </div>
                ))
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};


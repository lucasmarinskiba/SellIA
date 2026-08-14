'use client';

import { useState } from 'react';

export const Tabs = ({ defaultValue, children, className }: { defaultValue?: string; children: React.ReactNode; className?: string }) => {
  const [activeTab, setActiveTab] = useState(defaultValue || '');
  return <div className={className}>{children}</div>;
};

export const TabsList = ({ children, className }: { children: React.ReactNode; className?: string }) => (
  <div className={`flex border-b ${className || ''}`}>{children}</div>
);

export const TabsTrigger = ({ value, children, className }: { value: string; children: React.ReactNode; className?: string }) => (
  <button className={`px-4 py-2 ${className || ''}`}>{children}</button>
);

export const TabsContent = ({ value, children }: { value: string; children: React.ReactNode }) => <div>{children}</div>;


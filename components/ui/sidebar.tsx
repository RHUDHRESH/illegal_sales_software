'use client';

import React, { useState, useEffect } from 'react';
import { cn } from '@/lib/utils';

interface SidebarProps {
  open: boolean;
  setOpen: (open: boolean) => void;
  children: React.ReactNode;
}

export function Sidebar({ open, setOpen, children }: SidebarProps) {
  return (
    <aside
      className={cn(
        'relative hidden md:flex flex-col h-full border-r border-border bg-card transition-all duration-300',
        open ? 'w-64' : 'w-20'
      )}
    >
      {children}
    </aside>
  );
}

interface SidebarBodyProps {
  children: React.ReactNode;
  className?: string;
}

export function SidebarBody({ children, className }: SidebarBodyProps) {
  return (
    <div className={cn('flex flex-col h-full', className)}>
      {children}
    </div>
  );
}

interface SidebarLinkProps {
  link: {
    label: string;
    href: string;
    icon: React.ReactNode;
  };
}

export function SidebarLink({ link }: SidebarLinkProps) {
  return (
    <a
      href={link.href}
      className="flex items-center gap-3 px-4 py-2 rounded-lg text-neutral-700 dark:text-neutral-200 hover:bg-accent transition-colors"
    >
      {link.icon}
      <span>{link.label}</span>
    </a>
  );
}


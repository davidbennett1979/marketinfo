'use client'

import { ReactNode } from 'react'
import ChatInterface from '@/components/chat/ChatInterface'

interface ClientLayoutProps {
  children: ReactNode
}

export default function ClientLayout({ children }: ClientLayoutProps) {
  return (
    <>
      <ChatInterface />
      <div className="pt-8">
        {children}
      </div>
    </>
  )
}
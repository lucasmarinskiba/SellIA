'use client'

import { useEffect } from 'react'

export default function SellIADashboardPage() {
  useEffect(() => {
    // Redirect to sellia-brain dashboard
    window.location.href = '/sellia-brain'
  }, [])

  return null
}

/*
function DashboardInner() {
  const [filter, setFilter] = useState<string>('all')


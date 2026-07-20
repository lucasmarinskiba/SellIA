'use client'

import { useEffect, useState } from 'react'

import { getLocale, setLocale, subscribeLocale, t, type Locale } from './index'
import { LOCALE_LABELS, MESSAGES } from './messages'

export function useTranslation() {
  const [locale, setLocaleState] = useState<Locale>(() => getLocale())

  useEffect(() => {
    setLocaleState(getLocale())
    return subscribeLocale(() => setLocaleState(getLocale()))
  }, [])

  return {
    t,
    locale,
    setLocale: (l: Locale) => {
      setLocale(l)
      setLocaleState(l)
    },
    availableLocales: Object.keys(MESSAGES) as Locale[],
    labels: LOCALE_LABELS,
  }
}

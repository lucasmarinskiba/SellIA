'use client'

import { useState, useEffect, useCallback } from 'react'
import { missionsApi, Mission, BusinessDiagnostic, Playbook, DiagnosticRunResult } from '@/lib/missions'

export function useMissions(businessId?: string) {
  const [missions, setMissions] = useState<Mission[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchMissions = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await missionsApi.getMissions(businessId)
      setMissions(data)
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Error al cargar misiones')
    } finally {
      setLoading(false)
    }
  }, [businessId])

  useEffect(() => { fetchMissions() }, [fetchMissions])

  const approve = async (id: string) => {
    await missionsApi.approveMission(id)
    await fetchMissions()
  }

  const run = async (id: string) => {
    await missionsApi.runMission(id)
    await fetchMissions()
  }

  const cancel = async (id: string) => {
    await missionsApi.cancelMission(id)
    await fetchMissions()
  }

  return { missions, loading, error, refetch: fetchMissions, approve, run, cancel }
}

export function useDiagnostics(businessId?: string) {
  const [diagnostics, setDiagnostics] = useState<BusinessDiagnostic[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchDiagnostics = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await missionsApi.getDiagnostics(businessId)
      setDiagnostics(data)
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Error al cargar diagnósticos')
    } finally {
      setLoading(false)
    }
  }, [businessId])

  const runDiagnostics = async (): Promise<DiagnosticRunResult> => {
    setLoading(true)
    setError(null)
    try {
      const result = await missionsApi.runDiagnostics(businessId)
      setDiagnostics(result.diagnostics)
      return result
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Error al ejecutar diagnóstico')
      throw e
    } finally {
      setLoading(false)
    }
  }

  return { diagnostics, loading, error, fetchDiagnostics, runDiagnostics }
}

export function usePlaybooks() {
  const [playbooks, setPlaybooks] = useState<Playbook[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    missionsApi.getPlaybooks()
      .then(setPlaybooks)
      .catch((e: any) => setError(e?.response?.data?.detail || 'Error al cargar playbooks'))
      .finally(() => setLoading(false))
  }, [])

  return { playbooks, loading, error }
}

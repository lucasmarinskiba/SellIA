import { useEffect, useState } from 'react'
import { businessApi } from './business'
import { channelsApi, type ChannelConnection } from './channels'

export interface ChannelsState {
  businessId: string | null
  channels: ChannelConnection[]
  loading: boolean
  /** The connections could not be read at all (no session / backend down): never shown as "no connections". */
  unavailable: boolean
}

/** The signed-in account's real channel connections (same rows Canales manages), for any screen that shows them. */
export const useChannels = (): ChannelsState => {
  const [state, setState] = useState<ChannelsState>({ businessId: null, channels: [], loading: true, unavailable: false })

  useEffect(() => {
    let alive = true
    ;(async () => {
      try {
        const businesses = await businessApi.list()
        if (!businesses.length) {
          if (alive) setState({ businessId: null, channels: [], loading: false, unavailable: false })
          return
        }
        const channels = await channelsApi.list(businesses[0].id)
        if (alive) setState({ businessId: businesses[0].id, channels, loading: false, unavailable: false })
      } catch {
        if (alive) setState({ businessId: null, channels: [], loading: false, unavailable: true })
      }
    })()
    return () => {
      alive = false
    }
  }, [])

  return state
}

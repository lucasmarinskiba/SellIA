import * as SQLite from 'expo-sqlite'
import { apiClient } from './apiClient'

interface SyncQueue {
  id: string
  action: 'create' | 'update' | 'delete'
  entity_type: string
  entity_id: string
  data: Record<string, unknown>
  created_at: string
  synced: boolean
}

class OfflineSync {
  private db: SQLite.Database | null = null

  async init(): Promise<void> {
    try {
      this.db = await SQLite.openDatabaseAsync('sellia_offline.db')
      await this.createTables()
    } catch (error) {
      console.error('OfflineSync init error:', error)
    }
  }

  private async createTables(): Promise<void> {
    if (!this.db) return

    await this.db.execAsync(`
      CREATE TABLE IF NOT EXISTS sync_queue (
        id TEXT PRIMARY KEY,
        action TEXT NOT NULL,
        entity_type TEXT NOT NULL,
        entity_id TEXT NOT NULL,
        data TEXT NOT NULL,
        created_at TEXT NOT NULL,
        synced INTEGER DEFAULT 0
      );

      CREATE TABLE IF NOT EXISTS offline_cache (
        id TEXT PRIMARY KEY,
        entity_type TEXT NOT NULL,
        entity_id TEXT NOT NULL,
        data TEXT NOT NULL,
        cached_at TEXT NOT NULL,
        expires_at TEXT
      );

      CREATE INDEX IF NOT EXISTS idx_sync_synced ON sync_queue(synced);
      CREATE INDEX IF NOT EXISTS idx_cache_expires ON offline_cache(expires_at);
    `)
  }

  async queueAction(
    action: 'create' | 'update' | 'delete',
    entityType: string,
    entityId: string,
    data: Record<string, unknown>
  ): Promise<void> {
    if (!this.db) return

    const id = `${entityType}_${entityId}_${Date.now()}`
    await this.db.runAsync(
      'INSERT INTO sync_queue (id, action, entity_type, entity_id, data, created_at, synced) VALUES (?, ?, ?, ?, ?, ?, ?)',
      [id, action, entityType, entityId, JSON.stringify(data), new Date().toISOString(), 0]
    )
  }

  async syncQueue(): Promise<{ success: number; failed: number }> {
    if (!this.db) return { success: 0, failed: 0 }

    const queued = await this.db.allAsync<SyncQueue>(
      'SELECT * FROM sync_queue WHERE synced = 0 ORDER BY created_at ASC LIMIT 100'
    )

    let success = 0
    let failed = 0

    for (const item of queued) {
      try {
        const data = JSON.parse(item.data as unknown as string)

        switch (item.action) {
          case 'create':
            if (item.entity_type === 'comment') {
              await apiClient.addComment(
                item.entity_id,
                data.user_id,
                data.content,
                data.mentions
              )
            }
            break
          case 'update':
            if (item.entity_type === 'deal_stage') {
              await apiClient.updateDealStage(item.entity_id, data.stage)
            }
            break
        }

        await this.db.runAsync('UPDATE sync_queue SET synced = 1 WHERE id = ?', [item.id])
        success++
      } catch (error) {
        console.error(`Sync failed for ${item.id}:`, error)
        failed++
      }
    }

    return { success, failed }
  }

  async cacheData(
    entityType: string,
    entityId: string,
    data: Record<string, unknown>,
    expiresIn?: number
  ): Promise<void> {
    if (!this.db) return

    const id = `${entityType}_${entityId}`
    const expiresAt = expiresIn ? new Date(Date.now() + expiresIn).toISOString() : null

    await this.db.runAsync(
      `INSERT OR REPLACE INTO offline_cache (id, entity_type, entity_id, data, cached_at, expires_at)
       VALUES (?, ?, ?, ?, ?, ?)`,
      [id, entityType, entityId, JSON.stringify(data), new Date().toISOString(), expiresAt]
    )
  }

  async getCachedData(entityType: string, entityId: string): Promise<Record<string, unknown> | null> {
    if (!this.db) return null

    const cached = await this.db.getFirstAsync<{ data: string }>(
      `SELECT data FROM offline_cache
       WHERE entity_type = ? AND entity_id = ?
       AND (expires_at IS NULL OR expires_at > datetime('now'))`,
      [entityType, entityId]
    )

    if (cached) {
      return JSON.parse(cached.data)
    }
    return null
  }

  async clearExpired(): Promise<void> {
    if (!this.db) return
    await this.db.runAsync(`DELETE FROM offline_cache WHERE expires_at < datetime('now')`)
  }
}

export const offlineSync = new OfflineSync()

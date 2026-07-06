import type { SystemStatusResponse } from '@nova/api-contracts'
import type { SystemStatusViewModel } from '@/view-models'

export function mapSystemStatus(response: SystemStatusResponse): SystemStatusViewModel {
  return {
    status: response.status,
    version: response.version,
    subsystems: response.subsystems.map((subsystem) => ({
      name: subsystem.name,
      status: subsystem.status,
      message: subsystem.message,
    })),
  }
}

import type { HomeResponse } from '@nova/api-contracts'
import type { HomeViewModel } from '@/view-models'

export function mapHome(response: HomeResponse): HomeViewModel {
  return {
    cards: response.cards.map((card) => ({
      id: card.id,
      label: card.label,
      value: card.value,
      icon: card.icon,
    })),
    panels: response.panels.map((panel) => ({
      id: panel.id,
      title: panel.title,
      items: panel.items.map((item) => ({
        id: item.id,
        primary: item.primary,
        secondary: item.secondary,
        meta: item.meta ?? {},
      })),
    })),
  }
}

import { Button, Switch, Popover, PopoverContent, PopoverTrigger, SearchField, host, useValue } from '@hermes/plugin-sdk'
import { useEffect, useState } from 'react'
import { jsx, jsxs } from 'react/jsx-runtime'

const keyOf = (p, m) => `${p}::${m}`
const sectionStyle = { margin: '16px 0 8px', fontSize: 11, fontWeight: 650, color: 'var(--ui-text-secondary)' }
const gridStyle = { display: 'grid', gridTemplateColumns: 'repeat(2,minmax(0,1fr))', gap: 8 }
function Star({ filled = false }) {
  return jsx('svg', { width: 16, height: 16, viewBox: '0 0 24 24', 'aria-hidden': true, fill: filled ? 'currentColor' : 'none', stroke: 'currentColor', strokeWidth: 1.7,
    children: jsx('path', { d: 'm12 3 2.8 5.7 6.3.9-4.5 4.4 1.1 6.2-5.7-3-5.7 3 1.1-6.2-4.5-4.4 6.3-.9Z' }) })
}
export default {
  id: 'favorites-models', name: 'Избранные модели', defaultEnabled: true,
  description: 'Отдельная кнопка и карточки только выбранных тобой моделей.',
  register(ctx) {
    const valid = list => Array.isArray(list) ? [...new Set(list.filter(k => typeof k === 'string' && k.indexOf('::') > 0 && !k.endsWith('::')))] : []
    let saved = valid(ctx.storage.get('favorites', []))
    const listeners = new Set()
    function update(next) {
      saved = valid(next)
      ctx.storage.set('favorites', saved)
      for (const listener of listeners) listener(saved)
    }
    function FavoritesPanel() {
      const sessionId = useValue(host.state.focusedSessionId)
      const [favorites, setFavorites] = useState(saved)
      const [open, setOpen] = useState(false)
      const [query, setQuery] = useState('')
      const [showProviders, setShowProviders] = useState(() => ctx.storage.get('showProviders', false) === true)
      const [collapsed, setCollapsed] = useState(() => {
        const value = ctx.storage.get('collapsedProviders', {})
        return value && typeof value === 'object' && !Array.isArray(value) ? value : {}
      })
      function changeProviders(next) {
        setShowProviders(next)
        ctx.storage.set('showProviders', next)
        if (!next) setQuery('')
      }
      function toggleProvider(slug, expanded) {
        setCollapsed(previous => {
          const next = { ...previous, [slug]: expanded }
          ctx.storage.set('collapsedProviders', next)
          return next
        })
      }
      const [catalog, setCatalog] = useState(null)
      const [error, setError] = useState('')
      const [loading, setLoading] = useState(false)
      const [switching, setSwitching] = useState(false)
      useEffect(() => { listeners.add(setFavorites); return () => listeners.delete(setFavorites) }, [])
      useEffect(() => {
        if (!open) return
        let cancelled = false
        setLoading(true); setError('')
        host.request('model.options', { explicit_only: true, include_unconfigured: false, ...(sessionId ? { session_id: sessionId } : {}) })
          .then(data => { if (!cancelled) setCatalog(data) })
          .catch(e => { if (!cancelled) setError(`Не удалось загрузить модели: ${e.message || e}`) })
          .finally(() => { if (!cancelled) setLoading(false) })
        return () => { cancelled = true }
      }, [open, sessionId])
      function changeOpen(next) { setOpen(next); if (!next) setQuery('') }
      function toggleFavorite(p, m) {
        const k = keyOf(p, m)
        update(saved.includes(k) ? saved.filter(x => x !== k) : [...saved, k])
      }
      async function selectModel(p, m) {
        if (switching) return
        setSwitching(true)
        try {
          if (!host.models?.select) throw new Error('Для выбора модели нужна новая сборка Hermes. Перезапусти приложение после установки исправления.')
          const selected = await host.models.select({ model: m, provider: p })
          if (selected === true) {
            changeOpen(false)
          }
        } catch (e) { host.notifyError(`Модель не переключилась: ${e.message || e}`) }
        finally { setSwitching(false) }
      }
      const providers = catalog?.providers || []
      const availableKeys = new Set(providers.flatMap(p => (p.models || []).map(m => keyOf(p.slug, m))))
      const visibleFavorites = favorites.filter(k => availableKeys.has(k))
      const names = Object.fromEntries(providers.map(p => [p.slug, p.name || p.slug]))
      const q = query.trim().toLowerCase()
      function card(p, m, quick) {
        const favorite = favorites.includes(keyOf(p, m))
        const active = catalog?.model === m && catalog?.provider === p
        return jsxs('div', {
          style: { display: 'flex', alignItems: 'center', gap: 8, minWidth: 0, padding: 10, borderRadius: 10, border: `1px solid var(${active ? '--ui-accent' : '--ui-stroke-secondary'})`, background: 'var(--ui-bg-elevated)' },
          children: [
            jsxs('button', { type: 'button', disabled: switching, 'aria-label': quick ? `Выбрать ${m}` : `Модель ${m}`, title: m,
              onClick: () => quick ? selectModel(p, m) : toggleFavorite(p, m),
              style: { display: 'flex', flexDirection: 'column', flex: 1, minWidth: 0, gap: 4, padding: 0, background: 'transparent', border: 0, cursor: 'pointer', textAlign: 'left', color: 'var(--ui-text-primary)' },
              children: [jsx('span', { style: { fontSize: 12, fontWeight: 600, width: '100%', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }, children: m }, 'model'), jsx('span', { style: { fontSize: 11, color: 'var(--ui-text-tertiary)' }, children: names[p] || p }, 'provider')]
            }, 'pick'),
            jsx('button', { type: 'button', 'aria-label': favorite ? `Убрать из избранного ${m}` : `Добавить в избранное ${m}`,
              onClick: () => toggleFavorite(p, m),
              style: { display: 'flex', flexShrink: 0, padding: 4, background: 'transparent', border: 0, cursor: 'pointer', color: favorite ? 'var(--ui-accent)' : 'var(--ui-text-tertiary)' }, children: jsx(Star, { filled: favorite }) }, 'star')
          ]
        }, keyOf(p, m))
      }
      return jsxs(Popover, { open, onOpenChange: changeOpen, children: [
        jsx(PopoverTrigger, { asChild: true, children: jsx(Button, {
          type: 'button', variant: 'ghost', 'aria-label': 'Избранные модели', 'data-testid': 'favorites-models-button',
          title: 'Избранные модели',
          className: 'h-(--composer-control-size) shrink-0 rounded-md p-0', style: { width: 28, display: 'inline-flex', alignItems: 'center', justifyContent: 'center', WebkitAppRegion: 'no-drag' },
          children: jsx(Star, {})
        }) }, 'trigger'),
        jsx(PopoverContent, { variant: 'menu', side: 'top', align: 'end', sideOffset: 8,
          style: { width: 'min(560px,calc(100vw - 32px))', boxSizing: 'border-box', maxHeight: 'min(640px,75vh,var(--radix-popover-content-available-height,640px))', overflowY: 'auto', padding: 16, WebkitAppRegion: 'no-drag' },
          children: jsxs('div', { children: [
            jsxs('div', { style: { display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12, paddingBottom: 12, borderBottom: '1px solid var(--ui-stroke-secondary)' },
              children: [jsxs('div', { style: { display: 'flex', gap: 8, alignItems: 'center', fontWeight: 650 }, children: [jsx(Star, {}, 'icon'), jsx('span', { children: 'Избранные модели' }, 'title')] }, 'heading'), jsx(Button, { type: 'button', variant: 'outline', 'aria-label': 'Вернуться в чат', onClick: () => changeOpen(false), children: '← Вернуться в чат' }, 'back')]
            }, 'header'),
            jsx('p', { style: sectionStyle, children: 'БЫСТРЫЙ ВЫБОР — нажми карточку для переключения' }, 'quick-title'),
            visibleFavorites.length ? jsx('div', { style: gridStyle, children: visibleFavorites.map(k => { const at = k.indexOf('::'); return card(k.slice(0, at), k.slice(at + 2), true) }) }, 'favorites') : jsx('p', { style: sectionStyle, children: 'Пока пусто. Выбери избранное из установленных провайдеров ниже.' }, 'empty'),
            jsxs('div', { style: { display: 'flex', alignItems: 'center', gap: 12, marginTop: 20, paddingTop: 12, borderTop: '1px solid var(--ui-stroke-secondary)' }, children: [
              jsx('span', { style: { fontSize: 12, flex: 1, color: 'var(--ui-text-secondary)' }, children: 'Установленные провайдеры' }, 'label'),
              jsx(Switch, { 'aria-label': 'Установленные провайдеры', checked: showProviders, onCheckedChange: changeProviders }, 'toggle')
            ] }, 'catalog-toggle'),
            showProviders ? jsx(SearchField, { 'aria-label': 'Поиск модели', placeholder: 'Поиск модели…', value: query, onChange: setQuery, variant: 'box', containerClassName: 'mt-3 w-full' }, 'search') : null,
            error ? jsx('p', { role: 'alert', children: error }, 'error') : null,
            loading ? jsx('p', { style: sectionStyle, children: 'Загружаю каталог…' }, 'loading') : null,
            ...(showProviders ? providers.map(p => {
              const models = (p.models || []).filter(m => !q || `${m} ${p.name || ''} ${p.slug}`.toLowerCase().includes(q))
              const expanded = typeof collapsed[p.slug] === 'boolean' ? !collapsed[p.slug] : Boolean(q)
              return models.length ? jsxs('section', { children: [
                jsxs('button', {
                  type: 'button', 'aria-label': `Провайдер ${p.name || p.slug}`, 'aria-expanded': expanded,
                  onClick: () => toggleProvider(p.slug, expanded),
                  style: { display: 'flex', alignItems: 'center', gap: 8, width: '100%', padding: '10px 0', marginTop: 8, background: 'transparent', border: 0, cursor: 'pointer', textAlign: 'left', color: 'var(--ui-text-secondary)', fontSize: 12, fontWeight: 650 },
                  children: [jsx('span', { 'aria-hidden': true, children: expanded ? '▾' : '▸' }, 'arrow'), jsx('span', { children: p.name || p.slug }, 'name'), jsx('span', { style: { marginLeft: 'auto', fontWeight: 400, color: 'var(--ui-text-tertiary)' }, children: String(models.length) }, 'count')]
                }, 'heading'),
                expanded ? jsx('div', { style: gridStyle, children: models.slice(0, 100).map(m => card(p.slug, m, false)) }, 'grid') : null,
                expanded && models.length > 100 ? jsx('p', { style: sectionStyle, children: 'Показаны первые 100 моделей. Уточни поиск.' }, 'limit') : null
              ] }, p.slug) : null
            }) : []),
            showProviders && !loading && catalog && q && !providers.some(p => (p.models || []).some(m => `${m} ${p.name || ''} ${p.slug}`.toLowerCase().includes(q))) ? jsx('p', { style: sectionStyle, children: 'Ничего не найдено.' }, 'no-matches') : null
          ] })
        }, 'content')
      ] })
    }
    ctx.register({ area: 'composer.actions', id: 'favorites-models-button', order: 20, render: () => jsx(FavoritesPanel, {}) })
  }
}

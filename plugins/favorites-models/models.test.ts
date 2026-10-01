import { afterEach, describe, expect, it, vi } from 'vitest'
import { modelsHost, registerModelSelection } from './models'
let dispose: (() => void) | undefined
afterEach(() => { dispose?.(); dispose = undefined })
describe('native plugin model selection', () => {
  it('fails closed when native surface is absent', async () => {
    expect(await modelsHost.select({ model: 'a', provider: 'b' })).toBe(false)
  })
  it('delegates draft and live choices to the registered native action', async () => {
    const select = vi.fn(async () => true)
    dispose = registerModelSelection(select)
    const choice = { model: 'exact/model', provider: 'exact-provider' }
    expect(await modelsHost.select(choice)).toBe(true)
    expect(select).toHaveBeenCalledWith(choice)
  })
  it('preserves refused selection', async () => {
    dispose = registerModelSelection(async () => false)
    expect(await modelsHost.select({ model: 'a', provider: 'b' })).toBe(false)
  })
  it('propagates failure rather than reporting success', async () => {
    dispose = registerModelSelection(async () => { throw new Error('offline') })
    await expect(modelsHost.select({ model: 'a', provider: 'b' })).rejects.toThrow('offline')
  })
})

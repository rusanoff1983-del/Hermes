export interface PluginModelSelection {
  model: string
  provider: string
}
type ModelSelector = (selection: PluginModelSelection) => Promise<boolean>
let nativeSelect: ModelSelector | undefined
/** Installed by the app-wide focused model picker; never writes profile defaults. */
export function registerModelSelection(select: ModelSelector): () => void {
  nativeSelect = select
  return () => { if (nativeSelect === select) nativeSelect = undefined }
}
export const modelsHost = {
  /** Same action as the native picker, including sessionless draft selection. */
  select: async (selection: PluginModelSelection): Promise<boolean> => {
    if (!selection || typeof selection.model !== 'string' || !selection.model ||
      typeof selection.provider !== 'string' || !selection.provider) return false
    return nativeSelect ? nativeSelect(selection) : false
  }
}

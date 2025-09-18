declare module '*.vue' {
    import type { ComponentOptions } from 'vue'
    const component: ComponentOptions
    export default component
}

declare module '@vue/runtime-core' {
    export interface ComponentCustomProperties { }
}
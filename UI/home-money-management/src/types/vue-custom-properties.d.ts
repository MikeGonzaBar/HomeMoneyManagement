import '@vue/runtime-core';

export {};

declare module '@vue/runtime-core' {
  interface ComponentCustomProperties {
    $vuetify: any;
    $router: import('vue-router').Router;
  }
}

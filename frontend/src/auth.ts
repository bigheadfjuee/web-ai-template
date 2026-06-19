import Keycloak from 'keycloak-js'

export const keycloak = new Keycloak({
  url: '/auth',
  realm: 'app',
  clientId: 'vue-spa',
})

export function initKeycloak(): Promise<boolean> {
  return keycloak.init({
    onLoad: 'login-required',
    pkceMethod: 'S256',
  })
}

export function getToken(): string {
  return keycloak.token ?? ''
}

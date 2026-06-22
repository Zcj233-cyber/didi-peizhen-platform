import { createApp } from 'vue'
import router from './router'
import '../style.css'
// import './style.css'
import App from './App.vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import store from './store'
import PanelHead from './components/PanelHead.vue'

const localData = localStorage.getItem('pz_v3pz')
if(localData) {
  try {
    const parsed = JSON.parse(localData)
    if(parsed && parsed.menu && parsed.menu.routerList) {
      store.commit('dynamicMenu', parsed.menu.routerList)
      if(store.state.menu.routerList && Array.isArray(store.state.menu.routerList)) {
        store.state.menu.routerList.forEach(item => {
          router.addRoute('main', item)
        })
      }
    }
  } catch(e) {
    console.error('解析本地数据失败:', e)
  }
}

router.beforeEach((to, from) => {
  const token = localStorage.getItem('pz_token')
  if(!token && to.path !== '/login'){
    return '/login'
  } else if(token && to.path === '/login'){
    return '/'
  } else {
    return true
  }
})


const app = createApp(App)
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.component('PanelHead', PanelHead)
app.use(router)
app.use(ElementPlus)
app.use(store)
app.mount('#app')

import { createWebHashHistory, createRouter } from 'vue-router'
import Layout from '../views/Main.vue'
import Login from '../views/login/index.vue'
import Admin from '../views/auth/admin/index.vue'
import Group from '../views/auth/group/index.vue'
import Order from '../views/vppz/order/index.vue'
import Staff from '../views/vppz/staff/index.vue'
import Dashboard from '../views/dashboard/index.vue'
import AgentOverview from '../views/agent/overview/index.vue'
import AgentConfig from '../views/agent/config/index.vue'
import AgentDashboard from '../views/agent/dashboard/index.vue'


const routes = [
  { 
    path: '/',
    component: Layout,
    name: 'main',
    redirect: to => {
      const localData = localStorage.getItem('pz_v3pz')
      if (localData) {
        try {
          const routerList = JSON.parse(localData).menu.routerList
          // 找到第一个有 path 的叶子路由
          function findFirstPath(routes) {
            for (const r of routes) {
              if (r.children && r.children.length) {
                const found = findFirstPath(r.children)
                if (found) return found
              } else if (r.meta && r.meta.path) {
                return r.meta.path
              }
            }
            return null
          }
          const firstPath = findFirstPath(routerList)
          if (firstPath) return firstPath
        } catch (e) {
          console.error('redirect parse error:', e)
        }
      }
      return '/login'
    },
    children: [
      {
        path: 'dashboard',
        meta: { id: '1', name: '控制台', icon: 'Platform', path: '/dashboard', describe: '用于展示当前系统中的统计数据、统计报表及重要实时数据' },
        component: Dashboard
      },
      {
        path: 'auth',
        meta: { id: '2' ,name: '权限管理', icon: 'Grid' },
        children: [
          {
            path: '',
            alias: ['admin'],
            meta: { id: '1', name: '账号管理', icon: 'Avatar', path: '/auth/admin', describe: '管理员可以进行编辑，权限修改后需要登出才会生效' },
            component: Admin
          },
          {
            path: 'group',
            meta: { id: '2', name: '菜单管理', icon: 'Menu', path: '/auth/group', describe: '菜单规则通常对应一个控制器的方法,同时菜单栏数据也从规则中获取' },
            component: Group
          }
        ]
      },
      {
        path: 'vppz',
        meta: { id: '3', name: 'DIDI陪诊', icon: 'BellFilled' },
        children: [
          {
            path: '',
            alias: ['staff'],
            meta: { id: '1', name: '陪护管理', icon: 'Checked', path: '/vppz/staff', describe: '陪护师可以进行创建和修改，设置对应生效状态控制C端选择' },
            component: Staff
          },
          {
            path: 'order',
            meta: { id: '2', name: '订单管理', icon: 'List', path: '/vppz/order', describe: 'C端下单后可以查看所有订单状态，已支付的订单可以完成陪护状态修改' },
            component: Order
          }
        ]
      },
      {
        path: 'agent',
        meta: { id: '4', name: 'AI智能运营', icon: 'Monitor' },
        children: [
          {
            path: '',
            alias: ['overview'],
            meta: { id: '1', name: '运营数据助手', icon: 'ChatLineSquare', path: '/agent/overview', describe: '通过对话查询订单、用户等运营数据' },
            component: AgentOverview
          },
          {
            path: 'dashboard',
            meta: { id: '3', name: '智能运营中心', icon: 'DataAnalysis', path: '/agent/dashboard', describe: 'AI驱动的运营分析、预警与报告' },
            component: AgentDashboard
          },
          {
            path: 'config',
            meta: { id: '2', name: 'FAQ知识库', icon: 'Setting', path: '/agent/config', describe: '管理常见问题与回答' },
            component: AgentConfig
          }
        ]
      }
    ]
  },
  {
    path: '/login',
    component: Login
  },
]

const router = createRouter({
    routes,
    history: createWebHashHistory(),
})

export default router
import { createWebHashHistory, createRouter } from 'vue-router'

import Layout from '../pages/Main.vue'
import Home from '../pages/home/index.vue'
import Order from '../pages/order/index.vue'
import User from '../pages/user/index.vue'
import Login from '../pages/login/index.vue'
import createOrder from '../pages/createOrder/index.vue'
import detail from '../pages/detail/index.vue'
import AgentChat from '../pages/agent/chat/index.vue'
import AgentPlanning from '../pages/agent/planning/index.vue'
import AgentTriage from '../pages/agent/triage/index.vue'

const routes = [
  {
    path: '/',
    component: Layout,
    redirect: '/home',
    children: [
      {
        path: 'home',
        meta: {
          icon: 'home-o',
          name: '首页'
        },
        component: Home
      },
      {
        path: 'order',
        meta: {
          icon: 'orders-o',
          name: '订单'
        },
        component: Order
      },
      {
        path: 'user',
        meta: {
          icon: 'user-circle-o',
          name: '我的'
        },
        component: User
      }
    ]
  },
  {
    path: '/login',
    name:"login",
    component: Login

  },
  {
    path: '/createOrder',
    name:"createOrder",
    component: createOrder
  },
  {
    path: '/detail',
    name:"detail",
    component: detail
  },
  {
    path: '/agent/chat',
    name: 'agentChat',
    component: AgentChat
  },
  {
    path: '/agent/planning',
    name: 'agentPlanning',
    component: AgentPlanning
  },
  {
    path: '/agent/triage',
    name: 'agentTriage',
    component: AgentTriage
  },
]

export default createRouter({
  history: createWebHashHistory(),
  routes
})

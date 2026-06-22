
const localData = localStorage.getItem('pz_v3pz')
let parsedData
try {
    parsedData = localData ? JSON.parse(localData) : null
} catch (e) {
    parsedData = null
}

const state = parsedData && parsedData.menu ? parsedData.menu : {
    isCollapse: false,
    selectMenu: [],
    routerList: [],
    menuActive: '1-1'
}

const mutations = {
    collapseMenu(state) {
        state.isCollapse = !state.isCollapse
    },
    addMenu(state, payload) {
        if (state.selectMenu.findIndex(item => item.path === payload.path) === -1) {
            state.selectMenu.push(payload)
        }
    },
    closeMenu(state, payload) {
        const index = state.selectMenu.findIndex(val => val.name === payload.name)
        if (index !== -1) {
            state.selectMenu.splice(index, 1)
        }
    },
    dynamicMenu(state, payload) {
        if (!payload || !Array.isArray(payload)) {
            return
        }
        const modules = import.meta.glob('../views/**/**/*.vue')
        function routerSet(router) {
            if (!router || !Array.isArray(router)) {
                return
            }
            router.forEach(route => {
                if (!route.children) {
                    if (route.meta && route.meta.path) {
                        const url = `../views${route.meta.path}/index.vue`
                        route.component = modules[url]
                    }
                } else {
                    routerSet(route.children)
                }
            })
        }
        routerSet(payload)
        state.routerList = payload
    },
    updateMenuActive(state, payload) {
        state.menuActive = payload
    }
}

export default {
    state,
    mutations
}
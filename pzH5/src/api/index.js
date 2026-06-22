import request from '../utils/request'

export default {
    login(data) {
        return request.post('/login', data)
    },
    index() {
        return request.get('/index/index')
    },
    h5Companion() {
        return request.get('/h5/companion')
    },
    createOrder(data) {
        return request.post('/createOrder', data)
    },
    orderList(params) {
        return request.get('/order/list', { params })
    },
    orderDetail(params) {
        return request.get('/order/detail', { params })
    }
}
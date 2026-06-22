import request from "../utils/request";

export const getCode = (data) => {
    return request.post("/get/code", data);
}

export const userAuthentication = (data) => {
    return request.post("/user/authentication", data)
}

export const login = (data) => {
    return request.post("/login", data)
}

export const authAdmin = (params) => {
    return request.get("/auth/admin", { params })
}

export const userGetMenu = () => {
    return request.get("/user/getmenu")
}

export const userSetMenu = (data) => {
    return request.post("/user/setmenu", data)
}

export const menuList = (params) => {
    return request.get("/menu/list", { params })
}

export const menuSelectList = () => {
    return request.get("/menu/selectlist")
}

export const menuPermissions = () => {
    return request.get("/menu/permissions")
}

export const updateUser = (data) => {
    return request.post("/update/user", data)
}

export const photoList = () => {
    return request.get("/photo/list")
}

export const companion = (data) => {
    return request.post("/companion",data)
}

export const companionList = (params) => {
    return request.get("/companion/list", { params })
}

export const deleteCompanion = (data) => {
    return request.post("/delete/companion", data)
}

export const adminOrder = (params) => {
    return request.get("/admin/order", { params })
}

export const updateOrder = (data) => {
    return request.post("/update/order", data)
}
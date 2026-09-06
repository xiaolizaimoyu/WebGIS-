// 积分商城接口（前端 C）——对接后端 /api/mall
import request from './request'

// 商品列表：{ category?, page, size } -> { total, items }
export const listGoods = (params) => request.get('/mall/goods', { params })

// 商品详情
export const getGoods = (id) => request.get(`/mall/goods/${id}`)

// 兑换商品
export const redeemGoods = (id, quantity = 1) => request.post(`/mall/goods/${id}/redeem`, { quantity })

// 我的兑换记录
export const myRedeemRecords = (params) => request.get('/mall/my-records', { params })

// 商品分类
export const listCategories = () => request.get('/mall/categories')

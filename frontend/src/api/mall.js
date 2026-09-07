// 积分商城接口（前端 C）——对接后端 /api/mall
import request from './request'

// 商品列表：{ category?, page, size } -> { total, items }
export const listGoods = (params) => request.get('/mall/goods', { params })

// 商品分类（去重列表）
export const listCategories = () => request.get('/mall/categories')

// 商品详情
export const getGoods = (id) => request.get(`/mall/goods/${id}`)

// 兑换商品（后端按 goods_id 兑换一个，扣积分+减库存+生成订单）
export const redeemGoods = (id) => request.post(`/mall/exchange/${id}`)

// 我的兑换记录
export const myRedeemRecords = (params) => request.get('/mall/orders/mine', { params })

import axios from 'axios'

/**
 * 获取航班信息
 * @param {Object} params 查询参数
 * @returns {Promise} 请求的Promise对象
 */
export const getFlightInfo = (params) => {
  return axios.post('/api/ames/flight-info', {
    flight_date: params.flightDate || '',
    ac_reg: params.acReg || '',
    flight_no: params.flightNo || '',
    dep_code: params.depCode || '',
    arr_code: params.arrCode || '',
    page: params.page || 1,
    rows: params.rows || 50
  })
} 
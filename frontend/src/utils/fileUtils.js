/**
 * 文件解析工具类
 * 用于解析CSV、JSON和Excel文件
 */
import * as XLSX from 'xlsx';
import Papa from 'papaparse';

/**
 * 解析上传的文件，支持CSV、JSON和Excel文件
 * @param {File} file - 上传的文件对象
 * @returns {Promise<Object>} - 包含解析数据和列信息的对象
 */
export const parseFile = (file) => {
  return new Promise((resolve, reject) => {
    if (!file) {
      reject(new Error('未选择文件'));
      return;
    }

    const fileType = getFileExtension(file.name);
    
    try {
      if (fileType === 'csv') {
        parseCSV(file, resolve, reject);
      } else if (fileType === 'json') {
        parseJSON(file, resolve, reject);
      } else if (['xlsx', 'xls'].includes(fileType)) {
        parseExcel(file, resolve, reject);
      } else {
        reject(new Error(`不支持的文件类型: ${fileType}`));
      }
    } catch (error) {
      reject(new Error(`文件解析错误: ${error.message}`));
    }
  });
};

/**
 * 获取文件扩展名
 * @param {string} filename - 文件名
 * @returns {string} - 文件扩展名（小写）
 */
const getFileExtension = (filename) => {
  return filename.split('.').pop().toLowerCase();
};

/**
 * 解析CSV文件
 * @param {File} file - CSV文件对象
 * @param {Function} resolve - Promise resolve函数
 * @param {Function} reject - Promise reject函数
 */
const parseCSV = (file, resolve, reject) => {
  Papa.parse(file, {
    header: true,
    skipEmptyLines: true,
    complete: (results) => {
      if (results.errors && results.errors.length > 0) {
        reject(new Error(`CSV解析错误: ${results.errors[0].message}`));
        return;
      }

      const columns = results.meta.fields || [];
      resolve({
        data: results.data,
        columns: columns,
        total: results.data.length
      });
    },
    error: (error) => {
      reject(new Error(`CSV解析错误: ${error.message}`));
    }
  });
};

/**
 * 解析JSON文件
 * @param {File} file - JSON文件对象
 * @param {Function} resolve - Promise resolve函数
 * @param {Function} reject - Promise reject函数
 */
const parseJSON = (file, resolve, reject) => {
  const reader = new FileReader();
  
  reader.onload = (e) => {
    try {
      const data = JSON.parse(e.target.result);
      
      if (!Array.isArray(data)) {
        reject(new Error('JSON文件必须包含数组数据'));
        return;
      }
      
      if (data.length === 0) {
        resolve({ data: [], columns: [], total: 0 });
        return;
      }
      
      // 从第一个对象提取列
      const columns = Object.keys(data[0]);
      resolve({
        data: data,
        columns: columns,
        total: data.length
      });
    } catch (error) {
      reject(new Error(`JSON解析错误: ${error.message}`));
    }
  };
  
  reader.onerror = () => {
    reject(new Error('文件读取错误'));
  };
  
  reader.readAsText(file);
};

/**
 * 解析Excel文件
 * @param {File} file - Excel文件对象
 * @param {Function} resolve - Promise resolve函数
 * @param {Function} reject - Promise reject函数
 */
const parseExcel = (file, resolve, reject) => {
  const reader = new FileReader();
  
  reader.onload = (e) => {
    try {
      const data = new Uint8Array(e.target.result);
      const workbook = XLSX.read(data, { type: 'array' });
      
      // 获取第一个工作表
      const firstSheet = workbook.Sheets[workbook.SheetNames[0]];
      
      // 转换为JSON
      const jsonData = XLSX.utils.sheet_to_json(firstSheet, { header: 1 });
      
      if (jsonData.length < 2) {
        resolve({ data: [], columns: [], total: 0 });
        return;
      }
      
      // 第一行作为列名
      const columns = jsonData[0];
      
      // 剩余行作为数据
      const rows = jsonData.slice(1).map(row => {
        const obj = {};
        columns.forEach((col, index) => {
          obj[col] = row[index];
        });
        return obj;
      });
      
      resolve({
        data: rows,
        columns: columns,
        total: rows.length
      });
    } catch (error) {
      reject(new Error(`Excel解析错误: ${error.message}`));
    }
  };
  
  reader.onerror = () => {
    reject(new Error('文件读取错误'));
  };
  
  reader.readAsArrayBuffer(file);
};

/**
 * 获取解析文件的列选择
 * @param {Array} columns - 文件列名数组
 * @returns {Array} - 格式化后的列选项，适用于表格或图表
 */
export const getColumnOptions = (columns) => {
  if (!columns || !Array.isArray(columns)) {
    return [];
  }
  
  return columns.map(column => ({
    label: column,
    value: column,
    prop: column
  }));
}; 
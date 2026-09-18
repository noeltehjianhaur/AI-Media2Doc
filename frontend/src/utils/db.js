import { openDB, deleteDB } from 'idb'

const dbName = 'videoTasksDB'
const dbVersion = 2

let dbInstance = null

export async function initDB() {
  if (dbInstance) return dbInstance

  try {
    dbInstance = await openDB(dbName, dbVersion, {
      async upgrade(db, oldVersion, _newVersion, transaction) {
        let taskStore
        if (oldVersion < 1) {
          taskStore = db.createObjectStore('tasks', { keyPath: 'id', autoIncrement: true })
          taskStore.createIndex('md5', 'md5', { unique: false })
          taskStore.createIndex('createdAt', 'createdAt', { unique: false })
          taskStore.createIndex('fileName', 'fileName', { unique: false })
          taskStore.createIndex('contentStyle', 'contentStyle', { unique: false })
        } else {
          taskStore = transaction.objectStore('tasks')
        }
        if (oldVersion < 2) {
          if (taskStore.indexNames.contains('md5_contentStyle')) taskStore.deleteIndex('md5_contentStyle')
          taskStore.createIndex('md5_style_mode', ['md5', 'contentStyle', 'processingMode'], { unique: true })
          let cursor = await taskStore.openCursor()
          while (cursor) {
            const task = cursor.value
            if (!task.processingMode) {
              task.processingMode = 'audio'
              await cursor.update(task)
            }
            cursor = await cursor.continue()
          }
        }
      }
    })
    return dbInstance
  } catch (error) {
    console.error('数据库初始化失败:', error)
    throw error
  }
}

// 工具：序列化 transcriptionText
function serializeTranscriptionText(val) {
  if (Array.isArray(val)) {
    try {
      return JSON.stringify(val)
    } catch {
      return ''
    }
  }
  return val
}

// 工具：反序列化 transcriptionText
function deserializeTranscriptionText(val) {
  if (typeof val === 'string') {
    try {
      // 判断是否为 JSON 数组字符串
      const arr = JSON.parse(val)
      if (Array.isArray(arr) && arr.length && typeof arr[0] === 'object' && 'text' in arr[0]) {
        return arr
      }
    } catch {
      // 不是 JSON 字符串，直接返回原始字符串
    }
  }
  return val
}

export async function saveTask(taskData) {
  try {
    const db = await initDB()
    const taskToSave = {
      ...taskData,
      createdAt: new Date().toISOString(),
      contentStyle: taskData.contentStyle,
      processingMode: taskData.processingMode || 'audio',
      transcriptionText: serializeTranscriptionText(taskData.transcriptionText)
    }
    const taskId = await db.add('tasks', taskToSave)

    // 检查并保留最新的10条记录
    await cleanupOldTasks(db);

    return taskId; // 返回 taskId
  } catch (error) {
    console.error('保存任务失败:', error)
    throw error
  }
}

export async function updateTask(taskData) {
  const db = await initDB()
  const taskToSave = {
    ...taskData,
    processingMode: taskData.processingMode || 'audio',
    transcriptionText: serializeTranscriptionText(taskData.transcriptionText)
  }
  await db.put('tasks', taskToSave)
  return taskData.id
}

// 新增：清理旧任务，只保留最新的最大数量记录（取用户设置，默认10）
async function cleanupOldTasks(db) {
  try {
    let maxTasks = 10;
    try {
      const v = localStorage.getItem('maxRecords');
      if (v) {
        const n = parseInt(v);
        if (!isNaN(n) && n > 0) maxTasks = n;
      }
    } catch { }
    // 按创建时间降序排列获取所有任务
    const allTasks = await db.getAllFromIndex('tasks', 'createdAt');
    allTasks.sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt));

    // 如果任务数超过最大数量，则删除较旧的任务
    if (allTasks.length > maxTasks) {
      const tasksToDelete = allTasks.slice(maxTasks);
      for (const task of tasksToDelete) {
        await db.delete('tasks', task.id);
      }
      console.log(`已清理 ${tasksToDelete.length} 条旧任务记录，保留最新的 ${maxTasks} 条记录`);
    }
  } catch (error) {
    console.error('清理旧任务失败:', error);
  }
}

// 反序列化工具，批量处理任务数组
function deserializeTasks(tasks) {
  return tasks.map(task => ({
    ...task,
    processingMode: task.processingMode || 'audio',
    transcriptionText: deserializeTranscriptionText(task.transcriptionText)
  }))
}

export async function getAllTasks() {
  try {
    const db = await initDB()
    const tasks = await db.getAllFromIndex('tasks', 'createdAt')
    return deserializeTasks(tasks)
  } catch (error) {
    console.error('获取任务列表失败:', error)
    return []
  }
}

export async function getTaskByMd5(md5) {
  const db = await initDB()
  return db.getFromIndex('tasks', 'md5', md5)
}


export async function checkTaskExistsByMd5AndStyle(md5, contentStyle, processingMode = 'audio') {
  try {
    const db = await initDB()
    // 尝试使用组合索引查询
    try {
      const task = await db.getFromIndex('tasks', 'md5_style_mode', [md5, contentStyle, processingMode])
      return !!task // 有结果返回true，否则返回false
    } catch (e) {
      console.warn('组合索引查询失败，回退到手动筛选:', e)
      const tasks = await db.getAllFromIndex('tasks', 'md5', md5)
      return tasks.some(task => task.contentStyle === contentStyle && (task.processingMode || 'audio') === processingMode)
    }
  } catch (error) {
    console.error('检查任务失败:', error)
    throw error
  }
}

export const checkTaskExistsByMd5 = async (md5) => {
  try {
    const db = await initDB()
    const tasks = await db.getAllFromIndex('tasks', 'md5', md5)
    return tasks.length > 0
  } catch (error) {
    console.error('检查任务失败:', error)
    throw error
  }
}

export async function deleteTask(taskId) {
  try {
    const db = await initDB()
    await db.delete('tasks', taskId)
    return true
  } catch (error) {
    console.error('删除任务失败:', error)
    throw error
  }
}

export async function resetDatabase() {
  // 先关闭已有连接
  if (dbInstance) {
    dbInstance.close();
    dbInstance = null;
  }

  try {
    // 删除整个数据库
    await deleteDB(dbName);
    console.log('数据库已删除');

    // 重新初始化数据库
    dbInstance = await openDB(dbName, dbVersion, {
      upgrade(db) {
        // 创建全新的数据存储
        const taskStore = db.createObjectStore('tasks', { keyPath: 'id', autoIncrement: true })
        taskStore.createIndex('md5', 'md5', { unique: false })
        taskStore.createIndex('createdAt', 'createdAt', { unique: false })
        taskStore.createIndex('fileName', 'fileName', { unique: false })
        taskStore.createIndex('contentStyle', 'contentStyle', { unique: false })
        taskStore.createIndex('md5_style_mode', ['md5', 'contentStyle', 'processingMode'], { unique: true })

        console.log('数据库已重建');
      }
    })

    return true;
  } catch (error) {
    console.error('数据库重置失败:', error);
    return false;
  }
}

export async function getAnyTaskByMd5(md5) {
  try {
    const db = await initDB()
    const tasks = await db.getAllFromIndex('tasks', 'md5', md5)
    const result = tasks.length > 0 ? tasks[0] : null
    if (result) {
      result.transcriptionText = deserializeTranscriptionText(result.transcriptionText)
    }
    return result
  } catch (error) {
    console.error('根据MD5获取任务失败:', error)
    return null
  }
}

export async function getTaskByID(taskId) {
  try {
    const db = await initDB()
    const task = await db.get('tasks', taskId)
    if (task) {
      task.transcriptionText = deserializeTranscriptionText(task.transcriptionText)
    }
    return task
  } catch (error) {
    console.error('通过ID获取任务失败:', error)
    return null
  }
}

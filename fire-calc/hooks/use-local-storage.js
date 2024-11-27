(function () {
  const {ref, reactive} = Vue

  window.useLocalStorageBoolean = (key, defaultValue = false) => {
    const updateInitValue = () =>
      defaultValue ? !Boolean(localStorage.getItem(key)) : Boolean(localStorage.getItem(key))

    const val = ref(updateInitValue())

    watch(val, (val) => {
      if (!defaultValue) {
        val = !val
      }
      if (val) {
        localStorage.removeItem(key)
      } else {
        localStorage.setItem(key, '1')
      }
    })

    return val
  }

  window.useLocalStorageString = (key, defaultValue = '') => {
    const val = ref(localStorage.getItem(key) || defaultValue)
    watch(val, (val) => {
      if (val) {
        localStorage.setItem(key, val)
      } else {
        localStorage.removeItem(key)
      }
    })
    return val
  }

  window.useLocalStorageNumber = (key, defaultValue = 0) => {
    const val = ref(Number(localStorage.getItem(key)) || defaultValue)
    watch(val, (val) => {
      if (val) {
        localStorage.setItem(key, String(val))
      } else {
        localStorage.removeItem(key)
      }
    })
    return val
  }

  window.useLocalStorageObjectReactive = (key, defaultValue = {}) => {
    const val = reactive(JSON.parse(localStorage.getItem(key) || 'null') || defaultValue)
    watch(val, (val) => {
      if (val) {
        localStorage.setItem(key, JSON.stringify(val))
      } else {
        localStorage.removeItem(key)
      }
    })
    return val
  }


})()

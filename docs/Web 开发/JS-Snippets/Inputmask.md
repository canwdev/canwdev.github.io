#snippet [inputmask](https://robinherbots.github.io/Inputmask/#/documentation)

```html
<script src="https://cdnjs.cloudflare.com/ajax/libs/jquery/3.3.1/jquery.min.js"></script>  
<script src="https://rawgit.com/RobinHerbots/jquery.inputmask/3.x/dist/jquery.inputmask.bundle.js"></script>  
  
<h1><a href="https://robinherbots.github.io/Inputmask/#/documentation" target="_blank">Inputmask</a></h1>  
<label>IP Address</label>  
<input class="form-input" id="ipv4" name="ipv4" placeholder="xxx.xxx.xxx.xxx" type="text" />  
  
<script>  
  //input mask bundle ip address  
  var ipv4_address = $("#ipv4");  
  ipv4_address.inputmask({  
    alias: "ip",  
    greedy: true,  
    placeholder: " "  
  });  
</script>
```

`bun add inputmask`
```vue
<script lang="ts" setup="">  
import Inputmask from 'inputmask'  
  
const ipValue = ref('')  
const inputRef = ref()  
onMounted(() => {  
  const im = new Inputmask({  
    alias: 'ip',  
    greedy: true,  
    placeholder: ' ',  
  })  
  im.mask(inputRef.value)  
})  
</script>  
  
<template>  
    <input  
      v-model="ipValue"  
      type="text"  
      ref="inputRef"  
      placeholder="   .   .   .   "  
      class="ip-input"  
    />  
</template>  
  
<style lang="scss" scoped>  
  .ip-input {  
    max-width: 400px;  
    height: 32px;  
    background: #2e3133;  
    border-radius: 4px;  
    color: white;  
    border: none;  
    padding: 7px 10px;  
  }  
</style>
```

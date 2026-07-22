```ts
import {defineConfig, loadEnv} from 'vite'  
  
export default defineConfig(({mode}) => {  
  const env = loadEnv(mode, process.cwd())  
  const isTranslator = mode === 'translator'  
  
  return {  
    // 注意：.env.translator 文件也要放在该目录下，而不是项目跟目录  
    root: isTranslator ? 'src/views/translator' : '',  
    build: isTranslator  
      ? {  
          // 将输出目录调整到项目根目录  
          outDir: '../../../dist',  
          rollupOptions: {  
            input: {  
              index: 'src/views/translator/index.html',  
            },  
          },  
        }  
      : {},  
  }  
})
```
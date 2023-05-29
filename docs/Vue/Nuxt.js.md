## Nuxt 2 如何在 head() 中插入 script

```js
export default {
  head() {
    return {
      script: [
        // 插入jquery库
        {
          async: false,
          src: "https://code.jquery.com/jquery-3.7.0.min.js"
        },
        // 插入jsonLd
        {
          innerHTML: JSON.stringify({
            "@context": "https://schema.org/",
            "@type": "Product"
          }, null, 2),
          type: "application/ld+json"
        },
        // 插入谷歌统计数据
        {
          innerHTML: `
var dataLayer=[{
   'value': 0,
}];
`
        }
      ],
      __dangerouslyDisableSanitizers: ["script"]
    }
  }
}
```
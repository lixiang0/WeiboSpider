let viewHeight = document.documentElement.clientHeight // 获取可视区域的高度

function lazyload() {
  // 获取所有标记了lazyload的img标签
  let eles = document.querySelectorAll('img[data-original][lazyload]')

  // 遍历所有的img标签
  Array.prototype.forEach.call(eles, function (item, index) {
    let rect
    if (item.dataset.original === '')
      return
    rect = item.getBoundingClientRect()

    if (rect.bottom >= 0 && rect.top < viewHeight) {
      !function () {
        var img = new Image()
        img.src = item.dataset.original
        img.onload = function () {
          item.src = img.src
        }
        item.removeAttribute('data-original')
        item.removeAttribute('lazyload')
      }()
    }
  })
}

lazyload() //将首屏的图片加载，因为没有进行scroll，所以需要手动的调用一下

// scroll（页面滚动的时候）监听lazyload方法，获取所有标记了lazyload的img标签
document.addEventListener('scroll', lazyload)




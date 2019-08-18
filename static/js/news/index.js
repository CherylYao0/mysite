// static/js/news/index.js
/*=== bannerStart ===*/
$(() => {
    let $banner = $('.banner');
    let $picLi = $(".banner .pic li");
    let $prev = $('.banner .prev');
    let $next = $('.banner .next');
    let $tabLi = $('.banner .tab li');
    let index = 0;
    // 小原点
    $tabLi.click(function () {
        index = $(this).index();
        $(this).addClass('active').siblings('li').removeClass('active');
        $picLi.eq(index).fadeIn(1500).siblings('li').fadeOut(1500);
    });
    // 点击切换上一张
    $prev.click(() => {
        index--;
        if (index < 0) {
            index = $tabLi.length - 1
        }
        $tabLi.eq(index).addClass('active').siblings('li').removeClass('active');
        $picLi.eq(index).fadeIn(1500).siblings('li').fadeOut(1500);
    }).mousedown(() => false);
    // 点击切换下一张
    $next.click(() => {
        auto();
    }).mousedown(() => false);

    //  图片向前滑动
    function auto() {
        index++;
        index %= $tabLi.length;
        $tabLi.eq(index).addClass('active').siblings('li').removeClass('active');
        $picLi.eq(index).fadeIn(1500).siblings('li').fadeOut(1500);
    }

    // 定时器
    let timer = setInterval(auto, 2500);
    $banner.hover(() => {
        clearInterval(timer)
    }, () => {
        auto()
    })
});
/*=== bannerEnd ===*/
$(function () {
    // 新闻列表
    let $newNavLi = $('.news-nav ul li');   // 标签li
    let iPage = 1;                          // 默认第一页
    let iTotalPage = 1;                     // 默认总页数为1
    let iCurrentTagId = 0;                  // 默认分类标签为0
    let bIsLoadData = true;                 // 是否正在向后台加载数据

    fn_load_content();

    // 点击分类标签
    $newNavLi.click(function () {
        // 点击分类标签，则为点击的标签加上一个active的class属性
        // 并移除其他兄弟元素上的active的class属性
        $(this).addClass('active').siblings('li').removeClass('active');
        // 获取绑定在data-id属性上的tag_id
        let iClickTagId = $(this).children('a').attr('data-id');
        if (iClickTagId !== iCurrentTagId) {
            iCurrentTagId = iClickTagId;  // 记录当前分类id
            // 重置分页参数
            iPage = 1;
            iTotalPage = 1;
            fn_load_content()
        }

    });

    // 页面滚动加载
    $(window).scroll(function () {
        // 浏览器窗口高度
        let showHeigtht = $(window).height();
        // 整个网页高度
        let pageHeight = $(document).height();
        //页面可以滚动的距离
        let canScrollHeight = pageHeight - showHeigtht;
        // 页面滚动了多少， 整个是随着页面滚动实时变化的
        let nowScroll = $(document).scrollTop();
        if ((canScrollHeight - nowScroll) < 100) {
            if (!bIsLoadData) {
                bIsLoadData = true;
                //判断页数，去更新新闻，小于总数才加载
                if (iPage < iTotalPage) {
                    iPage += 1;
                    fn_load_content();

                } else {
                    message.showInfo('已全部加载，没有更多内容！');
                    $('a.btn-more').html('已全部加载，没有更多内容！')
                }

            }
        }
    });

    // 向后端获取新闻列表数据
    function fn_load_content() {
        $.ajax({
            url: '/news/',
            type: 'GET',
            data: {
                tag: iCurrentTagId,
                page: iPage
            },
            dataType: 'json',
            success: function (res) {
                if (res.errno === '0') {
                    iTotalPage = res.data.total_pages;
                    if (iPage === 1) {
                        // 第一页清空内容
                        $('.news-list').html('')
                    }
                    res.data.news.forEach(function (one_news) {
                        let content = `                  <li class="news-item">
                      <a href="https://www.shiguangkey.com/course/2432" class="news-thumbnail"
                         target="_blank">
                          <img src="${one_news.image_url}" alt="${one_news.title}"
                               title="${one_news.title}">
                      </a>
                      <div class="news-content">
                          <h4 class="news-title"><a
                                  href="#">${one_news.title}</a>
                          </h4>
                          <p class="news-details">${one_news.digest}</p>
                          <div class="news-other">
                              <span class="news-type">${one_news.tag_name}</span>
                              <span class="news-time">${one_news.update_time}</span>
                              <span class="news-author">${one_news.author}</span>
                          </div>
                      </div>
                  </li>`;
                        $('.news-list').append(content);
                    });
                    // $('.news-list').append($('<a href="javascript:void(0);" class="btn-more">滚动加载更多</a>'));
                    //数据加载完毕，设置正在加载数据变量为false，表示当前没有加载数据
                    bIsLoadData = false;
                    $('a.btn-more').html('滚动加载更多')
                } else {
                    // 加载失败，打印错误信息
                    message.showError(res.errmsg)
                }
            },
            error: function () {
                message.showError('服务器超时，请重试！')
            }
        });
    }
});
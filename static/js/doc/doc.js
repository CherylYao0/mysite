$(() => {
    let iPage = 1;       // 当前页面页数
    let iTotalPage = 1;      // 总页数
    let bIsLoadData =false;      // 是否正在加载
    fn_load_docs();      //  加载文件列表
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
        if ((canScrollHeight - nowScroll) < 100){
            if(!bIsLoadData){
                bIsLoadData = true;
                //判断页数，去更新新闻，小于总数才加载
                if(iPage < iTotalPage){
                    iPage += 1;
                    fn_load_docs();

                }else {
                    message.showInfo('已全部加载，没有更多内容！');
                    $('a.btn-more').html('已全部加载，没有更多内容！')
                }

            }
        }
    });

    // 获取docs信息
    function fn_load_docs() {
        $
            .ajax({
                url: '/doc/docs/',
                type: 'GET',
                data: {page: iPage},
                dataType: 'json'
            })
            .done((res) => {
                if (res.errno === '0') {
                    iTotalPage = res.data.total_page;
                    res.data.docs.forEach((doc) => {
                        let content = `<li class="pay-item">
                        <div class="pay-img doc"></div>
                           <img src="${ doc.image_url }" alt="" class="pay-img doc">
                        <div class="d-contain">
                            <p class="doc-title">${ doc.title }</p>
                            <p class="doc-desc">${ doc.desc }</p>

                            <!-- /www/?xxx -->
                            <a href="${ doc.file_url }" class="pay-price" download="${ doc.file_name }">下载</a>
                        </div>
                    </li>`;
                        $('.pay-list').append(content);
                        bIsLoadData = false;
                        $('a.btn-more').html('滚动加载更多');
                    })
                } else {
                    message.showError(res.errmsg)
                }
            })
            .fail(() => {
                message.showError('服务器超时，请重试！')
            })
    }
});
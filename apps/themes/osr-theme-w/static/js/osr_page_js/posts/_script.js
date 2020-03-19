
    var vue = new Vue({
      el: '#app',
      delimiters:['{[', ']}'],
      data:{
            ads:[],
            posts:{datas:[]},
            sort:"t-desc",
            pages:[],
            page:1,
            img_w_h:"?w=0&h=120",
            colors:[]
      },
      filters: {
            formatDate: function (time) {
              return irrformatDate(time, "yyyy-MM-dd hh:mm");
            }
      }
    })

    // 加载完页面执行
    $(document).ready(function(){
        vue.colors = osr_colors();
        var url_s = get_url_parameter()
        vue.page = get_obj_value(url_s, "page", vue.page)
        vue.sort = get_obj_value(url_s, "sort", vue.sort)
        get_posts(vue.page, vue.sort);
        get_global();
        nav_btn_active("post-sort", "post-sort-"+vue.sort);
    })

    function get_global(){
        var conditions = [
             {
                type:"image",
                name_regex:"post-list-ad-[0-9]+",
                result_key:"ads"
             }
        ];
        var d ={
            conditions:JSON.stringify(conditions),
            theme_name:"osr-theme-w"
        }
        var result = osrHttp("GET","/api/global/theme-data/display", d, args={not_prompt:true});
        result.then(function (r) {
            vue.ads = vue.ads.length > 0?r.data.medias.ads:[];
        });
    }

    //获取
    function get_posts(page, sort){
        nav_btn_active("post-sort", "post-sort-"+sort);
        vue.sort = sort;
        vue.page = page;
        if(sort=="t-desc"){
            sort = [{"issue_time":-1},{"update_time":-1}];
        }else if(sort=="t-asc"){
           sort = [{"issue_time":1},{"update_time":1}];
        }else{
            sort = [{"like": -1}, {"comment_num": -1}, {"pv": -1},{"issue_time": -1}];
        }

        d = {
            page:page,
            pre:12,
            status:"is_issued",
            sort:JSON.stringify(sort),
            unwanted_fields:JSON.stringify(["content", "imgs"])
        }

        var result = osrHttp("GET","/api/post", d, args={not_prompt:true});
        result.then(function (r) {
            $.each(r.data.posts.datas, function(index, value) {
                if(value["tags"].length>3 && value.brief_content.length>25){
                    value.brief_content = value.brief_content.slice(0, 25)
                }
                // if(value.editor=="markdown"){
                //     r.data.posts.datas[index]["brief_content"] = marked(value.brief_content);
                // }
            });
            vue.pages = paging(page_total=r.data.posts.page_total, current_page=r.data.posts.current_page);
            vue.posts = r.data.posts;
        });
        var url = window.location.pathname
                    +"?sort="+vue.sort
                    +"&page="+vue.page

        history_state(null, url);

    }


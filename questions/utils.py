from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator


def paginate(objects_list, request, per_page=10):
    paginator = Paginator(objects_list, per_page)
    page_number = request.GET.get('page', 1)

    try:
        page = paginator.page(page_number)
    except PageNotAnInteger:
        # В параметре не число (например ?page=abc) — показываем первую страницу
        page = paginator.page(1)
    except EmptyPage:
        # Если номер больше последней страницы — показываем последнюю, иначе первую
        try:
            num = int(page_number)
            page = paginator.page(paginator.num_pages if num > paginator.num_pages else 1)
        except (ValueError, TypeError):
            page = paginator.page(1)

    # Компактный список номеров страниц (с «...»), чтобы не рисовать тысячи ссылок
    page.elided_page_range = paginator.get_elided_page_range(
        page.number,
        on_each_side=2,
        on_ends=1,
    )
    return page

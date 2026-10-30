from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger


def paginate(objects_list, request, per_page=10):
    paginator = Paginator(objects_list, per_page)
    page_number = request.GET.get('page', 1)

    try:
        page = paginator.page(page_number)
    except PageNotAnInteger:
        # в параметре не число (например ?page=abc) - показываем первую страницу
        page = paginator.page(1)
    except EmptyPage:
        # такой страницы нет (например ?page=999 или ?page=-1) - тоже первая
        page = paginator.page(1)

    return page

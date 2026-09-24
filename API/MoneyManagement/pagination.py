from urllib.parse import parse_qsl, urlencode, urlsplit

from rest_framework.pagination import PageNumberPagination


class RelativePageNumberPagination(PageNumberPagination):
    """Page numbers with API-relative links and bounded client page sizes."""

    page_size_query_param = "page_size"
    max_page_size = 100

    def get_next_link(self):
        if not self.page.has_next():
            return None
        url = urlsplit(self.request.build_absolute_uri())
        query = dict(parse_qsl(url.query))
        query[self.page_query_param] = self.page.next_page_number()
        return f"{url.path}?{urlencode(query)}"

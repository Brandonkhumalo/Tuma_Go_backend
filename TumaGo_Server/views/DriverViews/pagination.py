from rest_framework.pagination import CursorPagination

class DeliveryCursorPagination(CursorPagination):
    page_size = 5
    ordering = '-start_time'  # must match a unique or indexed field
from typing import Any, List
from ninja_simple_jwt.auth.views.api import mobile_auth_router, HttpJwtAuth
from ninja import NinjaAPI
from .models import User, CourseMember, CourseContent,Comment,Course
from ninja.pagination import paginate, PaginationBase
from ninja import Schema

api = NinjaAPI()
api.add_router("/auth/", mobile_auth_router)
apiAuth = HttpJwtAuth()
@api.get("/users")
@paginate(PageNumberPagination, page_size=50)

class CustomPagination(PaginationBase):
    # only `skip` param, defaults to 5 per page
    class Input(Schema):
        skip: int

    class Output(Schema):
        items: List[Any] # `items` is a default attribute
        total: int
        per_page: int

    def paginate_queryset(self, queryset, pagination: Input, **params):
        skip = pagination.skip
        return {
            'items': queryset[skip : skip + 5],
            'total': queryset.count(),
            'per_page': 5,
        }
    
@api.get('mycourses/', auth=apiAuth, response=List[CourseMember])
def getMyCourses(request):
    user_id = User.objects.get(pk=request.user.id)
    mycourses = CourseMember.objects.filter(user_id=user_id)\
                            .select_related('course_id', 'user_id')
    return mycourses
@api.post('course/{id}/enroll/', auth=apiAuth, response=CourseMember)
def courseEnrollment(request, id:int):
    user_id = User.objects.get(pk=request.user.id)
    course = Course.objects.get(pk=id)

    enrollment = CourseMember.objects.create(user_id=user_id, course_id=course)
    return enrollment
@api.post('comments/', auth=apiAuth)
def postComment(request, data:Comment):
    user_id = User.objects.get(pk=request.user.id)
    content_id = CourseContent.objects.filter(id=data.content_id).first()
    coursemember = CourseMember.objects.filter(user_id=user_id, course_id=content_id.course_id)

    if coursemember.exists():
        Comment.objects.create(comment=data.comment, user_id=user_id, content_id=content_id)
        return "berhasil"
    else:
        return "tidak boleh komentar di sini"


    
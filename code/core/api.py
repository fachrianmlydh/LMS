import time
from datetime import datetime
from typing import List, Optional

from django.contrib.auth.models import User
from django.db import connection
from django.db.models import Count
from django.shortcuts import get_object_or_404
from django.test.utils import CaptureQueriesContext
from ninja import NinjaAPI, Schema
from ninja.errors import HttpError
from ninja.pagination import paginate
from ninja_simple_jwt.auth.ninja_auth import HttpJwtAuth
from ninja_simple_jwt.auth.views.api import mobile_auth_router

from .models import Comment, Course, CourseContent, CourseMember

api = NinjaAPI(title="Simple LMS API", urls_namespace="lms")
api.add_router("/auth/", mobile_auth_router)
auth = HttpJwtAuth()


# ---------- Schema ----------
class CourseIn(Schema):
    name: str
    description: str = "-"
    price: int = 10000


class CourseOut(Schema):
    id: int
    name: str
    description: str
    price: int
    teacher: str
    member_count: int

    @staticmethod
    def resolve_teacher(obj):
        return obj.teacher.username

    @staticmethod
    def resolve_member_count(obj):
        if hasattr(obj, "member_count"):  # sudah di-annotate (cepat)
            return obj.member_count
        return obj.coursemember_set.count()


class MemberOut(Schema):
    id: int
    course: int
    course_name: str
    roles: str

    @staticmethod
    def resolve_course(obj):
        return obj.course_id_id

    @staticmethod
    def resolve_course_name(obj):
        return obj.course_id.name


class ContentIn(Schema):
    name: str
    description: str = "-"
    video_url: Optional[str] = None
    parent_id: Optional[int] = None


class ContentOut(Schema):
    id: int
    name: str
    description: str
    video_url: Optional[str] = None
    course: int
    parent: Optional[int] = None

    @staticmethod
    def resolve_course(obj):
        return obj.course_id_id

    @staticmethod
    def resolve_parent(obj):
        return obj.parent_id_id


class CommentIn(Schema):
    comment: str


class CommentOut(Schema):
    id: int
    content: int
    username: str
    comment: str
    created_at: datetime

    @staticmethod
    def resolve_content(obj):
        return obj.content_id_id

    @staticmethod
    def resolve_username(obj):
        return obj.member_id.user_id.username


# ---------- Helper ----------
def current_user(request):
    return get_object_or_404(User, pk=request.user.id)


def own_course_or_403(user, course_id):
    course = get_object_or_404(Course.objects.select_related("teacher"), pk=course_id)
    if course.teacher_id != user.id:
        raise HttpError(403, "Hanya pengajar mata kuliah ini yang boleh melakukan ini")
    return course


def course_queryset():
    return Course.objects.select_related("teacher").annotate(
        member_count=Count("coursemember")
    )


# ---------- Mata kuliah ----------
@api.get("/courses", response=List[CourseOut])
@paginate
def list_courses(request, q: str = ""):
    qs = course_queryset().order_by("id")
    if q:
        qs = qs.filter(name__icontains=q)
    return qs


@api.get("/courses/{course_id}", response=CourseOut)
def course_detail(request, course_id: int):
    return get_object_or_404(course_queryset(), pk=course_id)


@api.post("/courses", auth=auth, response={201: CourseOut})
def create_course(request, data: CourseIn):
    user = current_user(request)
    course = Course.objects.create(
        name=data.name, description=data.description,
        price=data.price, teacher=user,
    )
    return 201, course


@api.put("/courses/{course_id}", auth=auth, response=CourseOut)
def update_course(request, course_id: int, data: CourseIn):
    course = own_course_or_403(current_user(request), course_id)
    course.name = data.name
    course.description = data.description
    course.price = data.price
    course.save()
    return course


@api.delete("/courses/{course_id}", auth=auth, response={204: None})
def delete_course(request, course_id: int):
    course = own_course_or_403(current_user(request), course_id)
    if course.coursemember_set.exists() or course.coursecontent_set.exists():
        raise HttpError(409, "Mata kuliah masih punya anggota/konten, hapus dulu")
    course.delete()
    return 204, None


# ---------- Pendaftaran ----------
@api.post("/courses/{course_id}/enroll", auth=auth, response={201: MemberOut})
def enroll(request, course_id: int):
    user = current_user(request)
    course = get_object_or_404(Course, pk=course_id)
    if course.teacher_id == user.id:
        raise HttpError(400, "Pengajar tidak perlu mendaftar ke mata kuliahnya sendiri")
    member, created = CourseMember.objects.get_or_create(course_id=course, user_id=user)
    if not created:
        raise HttpError(409, "Sudah terdaftar di mata kuliah ini")
    return 201, member


@api.get("/mycourses", auth=auth, response=List[MemberOut])
def my_courses(request):
    return CourseMember.objects.filter(user_id=request.user.id).select_related("course_id")


# ---------- Materi (konten) ----------
@api.get("/courses/{course_id}/contents", response=List[ContentOut])
def list_contents(request, course_id: int):
    get_object_or_404(Course, pk=course_id)
    return CourseContent.objects.filter(course_id=course_id).order_by("id")


@api.post("/courses/{course_id}/contents", auth=auth, response={201: ContentOut})
def create_content(request, course_id: int, data: ContentIn):
    course = own_course_or_403(current_user(request), course_id)
    parent = None
    if data.parent_id:
        parent = get_object_or_404(CourseContent, pk=data.parent_id, course_id=course)
    content = CourseContent.objects.create(
        name=data.name, description=data.description, video_url=data.video_url,
        course_id=course, parent_id=parent,
    )
    return 201, content


@api.put("/contents/{content_id}", auth=auth, response=ContentOut)
def update_content(request, content_id: int, data: ContentIn):
    content = get_object_or_404(CourseContent, pk=content_id)
    own_course_or_403(current_user(request), content.course_id_id)
    content.name = data.name
    content.description = data.description
    content.video_url = data.video_url
    content.save()
    return content


@api.delete("/contents/{content_id}", auth=auth, response={204: None})
def delete_content(request, content_id: int):
    content = get_object_or_404(CourseContent, pk=content_id)
    own_course_or_403(current_user(request), content.course_id_id)
    if content.coursecontent_set.exists():
        raise HttpError(409, "Konten masih punya sub-konten, hapus dulu")
    content.delete()  # komentar ikut terhapus (CASCADE)
    return 204, None


# ---------- Komentar ----------
@api.get("/contents/{content_id}/comments", response=List[CommentOut])
def list_comments(request, content_id: int):
    get_object_or_404(CourseContent, pk=content_id)
    return (Comment.objects.filter(content_id=content_id)
            .select_related("member_id__user_id").order_by("created_at"))


@api.post("/contents/{content_id}/comments", auth=auth, response={201: CommentOut})
def post_comment(request, content_id: int, data: CommentIn):
    user = current_user(request)
    content = get_object_or_404(CourseContent.objects.select_related("course_id"), pk=content_id)
    course = content.course_id
    member = CourseMember.objects.filter(course_id=course, user_id=user).first()
    if member is None and course.teacher_id == user.id:
        member = CourseMember.objects.create(course_id=course, user_id=user, roles="ast")
    if member is None:
        raise HttpError(403, "Hanya anggota mata kuliah yang boleh berkomentar")
    comment = Comment.objects.create(content_id=content, member_id=member, comment=data.comment)
    return 201, comment


@api.delete("/comments/{comment_id}", auth=auth, response={204: None})
def delete_comment(request, comment_id: int):
    comment = get_object_or_404(Comment.objects.select_related("member_id"), pk=comment_id)
    if comment.member_id.user_id_id != request.user.id:
        raise HttpError(403, "Hanya penulis komentar yang boleh menghapusnya")
    comment.delete()
    return 204, None


# ---------- Profiling ORM: versi lambat vs cepat ----------
def courses_slow():
    rows = []
    for c in Course.objects.all():                      # 1 query
        rows.append({
            "id": c.id, "name": c.name,
            "teacher": c.teacher.username,              # +1 query per course
            "members": c.coursemember_set.count(),      # +1 query per course
        })
    return rows


def courses_fast():
    qs = Course.objects.select_related("teacher").annotate(members=Count("coursemember"))
    return [{"id": c.id, "name": c.name, "teacher": c.teacher.username,
             "members": c.members} for c in qs]         # 1 query


def members_slow():
    rows = []
    for c in Course.objects.all():
        names = [m.user_id.username for m in c.coursemember_set.all()]
        rows.append({"id": c.id, "name": c.name, "members": names})
    return rows


def members_fast():
    qs = Course.objects.prefetch_related("coursemember_set__user_id")   # 3 query
    return [{"id": c.id, "name": c.name,
             "members": [m.user_id.username for m in c.coursemember_set.all()]}
            for c in qs]


def comments_slow():
    rows = []
    for cm in Comment.objects.order_by("id")[:200]:
        rows.append({
            "id": cm.id,
            "user": cm.member_id.user_id.username,
            "content": cm.content_id.name,
            "course": cm.content_id.course_id.name,
        })
    return rows


def comments_fast():
    qs = (Comment.objects
          .select_related("member_id__user_id", "content_id__course_id")
          .order_by("id")[:200])
    return [{"id": cm.id, "user": cm.member_id.user_id.username,
             "content": cm.content_id.name,
             "course": cm.content_id.course_id.name} for cm in qs]


SCENARIOS = {
    "courses": (courses_slow, courses_fast),
    "members": (members_slow, members_fast),
    "comments": (comments_slow, comments_fast),
}


@api.get("/profiling/{scenario}")
def profiling(request, scenario: str, mode: str = "slow"):
    """scenario: courses | members | comments. mode: slow | fast."""
    if scenario not in SCENARIOS or mode not in ("slow", "fast"):
        raise HttpError(404, "scenario: courses/members/comments, mode: slow/fast")
    func = SCENARIOS[scenario][0 if mode == "slow" else 1]
    start = time.perf_counter()
    with CaptureQueriesContext(connection) as ctx:
        data = func()
    return {
        "scenario": scenario, "mode": mode,
        "query_count": len(ctx),
        "duration_ms": round((time.perf_counter() - start) * 1000, 2),
        "total_rows": len(data),
        "sample": data[:2],
    }
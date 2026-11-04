import random

from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from core.models import Comment, Course, CourseContent, CourseMember


class Command(BaseCommand):
    help = "Isi data demo (user, mata kuliah, anggota, materi, komentar) untuk profiling ORM"

    def add_arguments(self, parser):
        parser.add_argument("--users", type=int, default=30)
        parser.add_argument("--courses", type=int, default=50)

    def handle(self, *args, **opts):
        if Course.objects.filter(name__startswith="Demo ").exists():
            self.stdout.write("Data demo sudah ada, dibatalkan.")
            return

        random.seed(42)
        pw = make_password("demo12345")
        existing = set(User.objects.filter(username__startswith="demo")
                       .values_list("username", flat=True))
        User.objects.bulk_create([
            User(username=f"demo{i}", email=f"demo{i}@example.com", password=pw)
            for i in range(1, opts["users"] + 1) if f"demo{i}" not in existing
        ])
        users = list(User.objects.filter(username__startswith="demo"))

        Course.objects.bulk_create([
            Course(name=f"Demo Kuliah {i}", description=f"Deskripsi demo {i}",
                   price=random.randint(1, 50) * 10000, teacher=random.choice(users))
            for i in range(1, opts["courses"] + 1)
        ])
        courses = list(Course.objects.filter(name__startswith="Demo "))

        members = []
        for c in courses:
            k = random.randint(min(5, len(users)), min(15, len(users)))
            for u in random.sample(users, k=k):
                members.append(CourseMember(course_id=c, user_id=u, roles="std"))
        CourseMember.objects.bulk_create(members)

        contents = []
        for c in courses:
            for j in range(1, random.randint(3, 6) + 1):
                contents.append(CourseContent(
                    name=f"Materi {j} - {c.name}", description="Materi demo", course_id=c))
        CourseContent.objects.bulk_create(contents)

        by_course = {}
        for m in CourseMember.objects.filter(course_id__in=courses):
            by_course.setdefault(m.course_id_id, []).append(m)
        comments = []
        for ct in CourseContent.objects.filter(course_id__in=courses):
            for k in range(random.randint(2, 8)):
                m = random.choice(by_course[ct.course_id_id])
                comments.append(Comment(content_id=ct, member_id=m,
                                        comment=f"Komentar demo {k + 1} pada {ct.name}"))
        Comment.objects.bulk_create(comments)

        self.stdout.write(self.style.SUCCESS(
            f"Selesai: {len(users)} user, {len(courses)} matkul, {len(members)} anggota, "
            f"{len(contents)} materi, {len(comments)} komentar")) 
from django.template import loader
from django.shortcuts import render
from .models import User,Course, CourseMember, Comment
from django.db.models import Max, Min, Avg, Count
from django.core import serializers
from django.http import JsonResponse
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.views.decorators.http import require_POST
# Create your views here.

def core(request):
   #return HttpResponse("Selamat Datang - e-LMS!")
   return render(request, "core/home.html")

def statistik(request):
    return render(request, "core/statistik.html")

def statistik_from_api(request):
    return render(request, "core/statistik_from_api.html")

def users(request):
  myusers = User.objects.all().values()
  template = loader.get_template('all_users.html')
  context = {
    'myusers': myusers,
  }
  return HttpResponse(template.render(context, request))

#User.objects.create_user(username="usertesting", email="usertest@email.com", password="sanditesting")
#Course.objects.create(name=row['name'], description=row['description'], price=row['price'], teacher=User.objects.get(pk=1))

def courseStat(request):
    # Ambil semua data course
    courses = Course.objects.all()

    # Hitung statistik harga
    stats = courses.aggregate(
        max_price=Max('price'),
        min_price=Min('price'),
        avg_price=Avg('price')
    )

    # Ambil course dengan harga termurah & termahal
    cheapest = Course.objects.filter(price=stats['min_price'])
    expensive = Course.objects.filter(price=stats['max_price'])

    # Ambil course terpopuler & tidak populer (berdasarkan jumlah member)
    popular = (
        Course.objects
        .annotate(member_count=Count('coursemember'))
        .order_by('-member_count')[:5]
    )
    unpopular = (
        Course.objects
        .annotate(member_count=Count('coursemember'))
        .order_by('member_count')[:5]
    )

    # Hasil akhir
    result = {
        'course_count': courses.count(),
        'courses': stats,
        'cheapest': serializers.serialize('python', cheapest),
        'expensive': serializers.serialize('python', expensive),
        'popular': serializers.serialize('python', popular),
        'unpopular': serializers.serialize('python', unpopular),
    }

    return JsonResponse(result, safe=False)

def userStatistics(request):
    # 1ï¸âƒ£ Semua user non-admin
    non_admin_users = User.objects.filter(is_staff=False, is_superuser=False)
    total_non_admin_users = non_admin_users.count()

    # 2ï¸âƒ£ User yang membuat course
    users_with_courses = User.objects.filter(course__isnull=False).distinct()
    total_users_with_courses = users_with_courses.count()

    # 3ï¸âƒ£ User tanpa course
    users_without_courses = non_admin_users.exclude(
        id__in=users_with_courses.values_list('id', flat=True)
    )
    total_users_without_courses = users_without_courses.count()

    # 4ï¸âƒ£ Rata-rata jumlah course yang diikuti per user
    avg_courses_per_user = (
        CourseMember.objects.values('user_id')
        .annotate(total=Count('course_id'))
        .aggregate(avg_courses=Avg('total'))['avg_courses'] or 0
    )

    # 5ï¸âƒ£ User yang mengikuti course terbanyak
    top_user = (
        CourseMember.objects.values('user_id')
        .annotate(total=Count('course_id'))
        .order_by('-total')
        .first()
    )

    top_user_data = {}
    if top_user:
        top_user_instance = User.objects.get(id=top_user['user_id'])
        top_user_data = {
            "id": top_user_instance.id,
            "username": top_user_instance.username,
            "email": top_user_instance.email,
            "total_courses": top_user['total']
        }

    # 6ï¸âƒ£ Daftar user tanpa course sama sekali
    users_no_courses = non_admin_users.exclude(
        id__in=CourseMember.objects.values_list('user_id', flat=True)
    )
    users_no_courses_list = list(
        users_no_courses.values('id', 'username', 'email')
    )

    # 7ï¸âƒ£ Total komentar (melalui member â†’ user)
    total_comments_all = Comment.objects.count()
    total_comments_non_admin = Comment.objects.filter(
        member_id__user_id__in=non_admin_users
    ).count()


    # 8ï¸âƒ£ User dengan komentar terbanyak (opsional tapi berguna)
    top_commenter = (
        Comment.objects
        .values('member_id__user_id')
        .annotate(total_comments=Count('id'))
        .order_by('-total_comments')
        .first()
    )

    top_commenter_data = {}
    if top_commenter:
        user_instance = User.objects.get(id=top_commenter['member_id__user_id'])
        top_commenter_data = {
            "id": user_instance.id,
            "username": user_instance.username,
            "email": user_instance.email,
            "total_comments": top_commenter['total_comments']
        }

    # 9ï¸âƒ£ Hasil akhir
    result = {
        "total_non_admin_users": total_non_admin_users,
        "total_users_with_courses": total_users_with_courses,
        "total_users_without_courses": total_users_without_courses,
        "average_courses_per_user": avg_courses_per_user,
        "top_user": top_user_data,
        "users_no_courses": users_no_courses_list,
        "total_comments_all": total_comments_all,
        "total_comments_non_admin": total_comments_non_admin,
        "top_commenter": top_commenter_data,
    }
    return JsonResponse(result, safe=False)

def users(request):
  myusers = User.objects.all().values()
  template = loader.get_template('all_users.html')
  context = {
    'myusers': myusers,
  }
  return HttpResponse(template.render(context, request))

# 1. Insert data User
def insert_user(request):
    user, created = User.objects.get_or_create(
        username="usertesting",
        defaults={"email": "usertest@email.com"}
    )

    if created:
        user.set_password("sanditesting")
        user.save()

    return JsonResponse({
        "message": "User berhasil ditambahkan" if created
                   else "User sudah tersedia",
        "id": user.id,
        "username": user.username,
        "email": user.email,
    })


# 2. Insert data Course
def insert_course(request):
    teacher = get_object_or_404(User, pk=1)

    course = Course.objects.create(
        name="Pemrograman Python",
        description="Belajar dasar pemrograman Python",
        price=150000,
        teacher=teacher,
    )

    return JsonResponse({
        "message": "Course berhasil ditambahkan",
        "id": course.id,
        "name": course.name,
        "teacher": course.teacher.username,
    })


# 3. Select semua User, tampilkan dalam HTML
def user_list(request):
    users = User.objects.all().order_by("id")
    return render(request, "users.html", {"users": users})


# 4. Select semua User, tampilkan sebagai JSON
def user_json(request):
    users = User.objects.all().values(
        "id", "username", "email", "first_name", "last_name"
    )
    return JsonResponse(list(users), safe=False)


# 5. Select satu User berdasarkan ID, tampilkan dalam HTML
def user_detail(request, pk):
    user = get_object_or_404(User, pk=pk)
    return render(request, "user_detail.html", {"user": user})


# 6. Select User dengan kondisi WHERE
def search_user(request):
    username = request.GET.get("username", "")
    users = User.objects.filter(
        username__icontains=username
    ).order_by("id")

    return render(request, "users.html", {"users": users})


# 7. Update data User
@require_POST
def update_user(request, pk):
    user = get_object_or_404(User, pk=pk)
    user.email = request.POST.get("email", user.email)
    user.save()

    return JsonResponse({
        "message": "User berhasil diupdate",
        "id": user.id,
        "email": user.email,
    })


# 8. Delete satu User
@require_POST
def delete_user(request, pk):
    user = get_object_or_404(User, pk=pk)
    username = user.username
    user.delete()

    return JsonResponse({
        "message": f"User {username} berhasil dihapus"
    })


# 9. Delete semua Course
@require_POST
def delete_all_courses(request):
    total, details = Course.objects.all().delete()

    return JsonResponse({
        "message": "Proses penghapusan Course selesai",
        "deleted_count": total,
        "details": details,
    })


# 10. Delete semua User kecuali ID tertentu
@require_POST
def delete_users_except(request, pk):
    # Contoh: pertahankan user dengan ID pk
    users = User.objects.exclude(pk=pk)
    total, details = users.delete()

    return JsonResponse({
        "message": f"User selain ID {pk} telah diproses",
        "deleted_count": total,
        "details": details,
    })
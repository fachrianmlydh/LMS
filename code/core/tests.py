from django.test import TestCase
from django.contrib.auth.models import User
from .models import Course, CourseMember, CourseContent, Enrollment
from django.core.exceptions import ValidationError


class CourseModelTest(TestCase):

    def setUp(self):
        # Buat user
        self.teacher = User.objects.create(username='teacher1')
        
        # Buat course
        self.course = Course.objects.create(
            name="Pemrograman Django",
            description="Belajar Django",
            price=150000,
            teacher=self.teacher
        )

    def test_course_creation(self):
        # Pastikan course berhasil dibuat
        course = Course.objects.get(name="Pemrograman Django")
        self.assertEqual(course.price, 150000)
        self.assertEqual(course.teacher.username, 'teacher1')
        self.assertEqual(str(course), course.name + " : " + str(course.price))

class CourseMemberModelTest(TestCase):

    def setUp(self):
        # Buat user dan course
        self.teacher = User.objects.create(username='teacher1')
        self.student = User.objects.create(username='student1')
        self.course = Course.objects.create(name="Pemrograman Django", teacher=self.teacher)

    def test_course_member_creation(self):
        # Buat subscriber untuk course
        member = CourseMember.objects.create(course_id=self.course, user_id=self.student, roles='std')

        # Pastikan CourseMember berhasil dibuat
        self.assertEqual(member.user_id.username, 'student1')
        self.assertEqual(member.roles, 'std')

class CourseContentModelTest(TestCase):

    def setUp(self):
        # Buat user dan course
        self.teacher = User.objects.create(username='teacher1')
        self.course = Course.objects.create(name="Pemrograman Django", teacher=self.teacher)

    def test_course_content_creation(self):
        # Buat konten untuk course
        content = CourseContent.objects.create(
            name="Pengenalan Django",
            course_id=self.course,
            description="Materi dasar tentang Django"
        )

        # Pastikan CourseContent berhasil dibuat
        self.assertEqual(content.course_id.name, "Pemrograman Django")
        self.assertEqual(content.name, "Pengenalan Django")
        self.assertEqual(str(content), '[' + str(content.course_id) + '] ' + content.name)

class CourseQueryTest(TestCase):

    def setUp(self):
        self.teacher1 = User.objects.create(username='teacher1')
        self.teacher2 = User.objects.create(username='teacher2')
        Course.objects.create(name="Django", teacher=self.teacher1)
        Course.objects.create(name="Flask", teacher=self.teacher2)

    def test_course_retrieval_by_teacher(self):
        # Query kursus yang diajarkan oleh teacher1
        courses = Course.objects.filter(teacher=self.teacher1)

        # Pastikan hanya ada satu course yang ditemukan dan itu milik teacher1
        self.assertEqual(courses.count(), 1)
        self.assertEqual(courses.first().name, "Django")



class CourseValidationTest(TestCase):

    def setUp(self):
        self.teacher = User.objects.create(username='teacher1')

    def test_invalid_price(self):
        # Coba membuat course dengan harga negatif
        course = Course(
            name="Pemrograman Django",
            description="Belajar Django",
            price=-10000,  # Harga tidak valid
            teacher=self.teacher
        )

        # Pastikan ValidationError muncul saat disimpan
        with self.assertRaises(ValidationError):
            course.full_clean()  # Memicu validasi manual

    def test_empty_name(self):
        # Coba membuat course tanpa nama
        course = Course(
            name="",  # Nama kosong
            description="Belajar Django",
            price=100000,
            teacher=self.teacher
        )

        # Pastikan ValidationError muncul
        with self.assertRaises(ValidationError):
            course.full_clean()

class CourseFilteringTest(TestCase):

    def setUp(self):
        self.teacher = User.objects.create(username='teacher1')
        Course.objects.create(name="Kursus 1", price=100000, teacher=self.teacher)
        Course.objects.create(name="Kursus 2", price=200000, teacher=self.teacher)
        Course.objects.create(name="Kursus 3", price=300000, teacher=self.teacher)

    def test_filter_courses_by_price(self):
        # Filter kursus dengan harga di bawah 200000
        affordable_courses = Course.objects.filter(price__lt=200000)

        # Pastikan hanya ada satu course yang sesuai
        self.assertEqual(affordable_courses.count(), 1)
        self.assertEqual(affordable_courses.first().name, "Kursus 1")



class EnrollmentTestCase(TestCase):

    def setUp(self):
        # Membuat data dummy untuk pengujian
        self.teacher = User.objects.create(username='teacher1')
        self.student = User.objects.create(username='student1')
        self.course = Course.objects.create(
            name="Pemrograman Python",
            description="Kursus Python tingkat dasar",
            price=50000,
            teacher=self.teacher
        )

    def test_enrollment_success(self):
        # Simulasi siswa mendaftar kursus
        enrollment = Enrollment.objects.create(
            course=self.course,
            student=self.student,
            status='paid'
        )

        # Pastikan siswa berhasil terdaftar di kursus
        self.assertEqual(enrollment.course.name, "Pemrograman Python")
        self.assertEqual(enrollment.student.username, "student1")
        self.assertEqual(enrollment.status, 'paid')

    def test_course_full(self):
        # Simulasi kursus penuh (misalnya kuota maksimal)
        self.course.max_students = 1
        self.course.save()

        # Daftarkan siswa pertama (harus berhasil)
        enrollment1 = Enrollment.objects.create(course=self.course, student=self.student, status='paid')

        # Simulasi siswa kedua mencoba mendaftar (harus gagal)
        student2 = User.objects.create(username='student2')
        with self.assertRaises(Exception):
            Enrollment.objects.create(course=self.course, student=student2, status='paid')
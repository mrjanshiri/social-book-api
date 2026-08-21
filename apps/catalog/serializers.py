from rest_framework import serializers
from .models import Author, Publisher, Category, Book
from apps.reviews.serializers import ReviewSerializer


class AuthorSerializer(serializers.ModelSerializer):
    books = serializers.StringRelatedField(many=True, read_only=True)

    class Meta:
        model = Author
        fields = ['id', 'name', 'bio', 'birth_date', 'books']

class PublisherSerializer(serializers.ModelSerializer):
    books = serializers.StringRelatedField(many=True, read_only=True)

    class Meta:
        model = Publisher
        fields = ['id', 'name', 'address', 'books']

class CategorySerializer(serializers.ModelSerializer):
    books = serializers.StringRelatedField(many=True, read_only=True)

    class Meta:
        model = Category
        fields = ['id', 'name', 'books']


class BookSerializer(serializers.ModelSerializer):
    # برای خواندن: نمایش نام نویسنده، ناشر، عنوان دسته بندی ها
    author = serializers.StringRelatedField(read_only=True)
    publisher = serializers.StringRelatedField(read_only=True)
    categories = serializers.StringRelatedField(many=True, read_only=True)
    reviews = ReviewSerializer(many=True, read_only=True) # برای نمایش ریویوها

    # برای نوشتن (POST/PUT): انتظار ID نویسنده، ناشر، و لیست ID دسته بندی ها را داریم
    # اگر میخواهید از طریق API نویسنده، ناشر و دسته بندی ها را هنگام ساخت کتاب مشخص کنید:
    author_id = serializers.PrimaryKeyRelatedField(
        queryset=Author.objects.all(),
        source='author', # به فیلد author در مدل اشاره میکند
        write_only=True # فقط برای نوشتن استفاده شود، در پاسخ نمایش داده نشود
    )
    publisher_id = serializers.PrimaryKeyRelatedField(
        queryset=Publisher.objects.all(),
        source='publisher',
        write_only=True,
    )
    category_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Category.objects.all(),
        source='categories',
        write_only=True
    )

    class Meta:
        model = Book
        fields = [
            'id', 'title', 'author', 'publisher', 'categories', 'publication_date',
            'isbn', 'pages', 'description', 'average_rating', 'reviews',
            'author_id', 'publisher_id', 'category_ids' # فیلدهای جدید برای نوشتن
        ]
        # اگر از read_only_fields استفاده میکنید، فیلدهایی که فقط برای نمایش هستند را اینجا نگه دارید
        # و فیلدهایی که قرار است از طریق API تنظیم شوند (مثل average_rating, author, publisher, categories, reviews)
        # را از read_only_fields حذف کنید.
        # اما چون ما از write_only=True استفاده کردیم، نیازی به حذف از read_only_fields نیست.
        # با این حال، اگر بخواهید author, publisher, categories, reviews را هم در پاسخ GET ببینید و هم بتوانید POST کنید،
        # باید اول آنها را از read_only_fields حذف کرده و سپس از PrimaryKeyRelatedField بدون write_only=True استفاده کنید.
        # اما برای سادگی، معمولا از فیلدهای جداگانه برای نوشتن (write_only) استفاده میشود.

        # برای این مثال، فرض میکنیم author, publisher, categories, reviews فقط برای نمایش هستند
        # و author_id, publisher_id, category_ids برای تنظیم روابط در POST/PUT استفاده میشوند.
        read_only_fields = ['average_rating', 'author', 'publisher', 'categories', 'reviews']

    # اگر میخواهید منطق پیچیده تری داشته باشید، میتوانید متدهای create و update را override کنید.
    # برای مثال، برای مدیریت ManyToMany فیلد categories:
    def create(self, validated_data):
        author_id = validated_data.pop('author') # author_id که از write_only دریافت شده
        publisher_id = validated_data.pop('publisher') # publisher_id اختیاری است
        category_ids = validated_data.pop('categories', []) # categories لیست ID ها

        book = Book.objects.create(author=author_id, publisher=publisher_id, **validated_data)

        book.categories.set(category_ids) # تنظیم دسته بندی ها

        return book

    # متد update را نیز باید به همین ترتیب override کنید اگر نیاز به بروزرسانی دارید.
    def update(self, instance, validated_data):
        # ابتدا فیلدهایی که فقط برای نوشتن (write_only) تعریف شده اند را از validated_data جدا میکنیم.
        # اینها همان ID هایی هستند که برای تنظیم روابط استفاده میشوند.
        author_obj = validated_data.pop('author', None)
        publisher_obj = validated_data.pop('publisher', None)
        category_objs = validated_data.pop('categories', []) # لیست اشیاء Category

        # اگر author_obj, publisher_obj, یا category_objs ارسال شده باشند، آنها را به instance اختصاص میدهیم.
        # در غیر این صورت، مقدار فعلی instance حفظ میشود.
        if author_obj:
            instance.author = author_obj
        if publisher_obj:
            instance.publisher = publisher_obj

        # اگر دسته بندی ها (category_objs) ارسال شده باشند، رابطه ManyToMany را تنظیم میکنیم.
        # اگر category_objs خالی باشد، به این معنی است که کاربر خواسته دسته بندی ها را پاک کند یا تغییری نداده.
        # در اینجا ما فرض میکنیم اگر category_ids ارسال شود، میخواهیم آن را جایگزین کنیم.
        # اگر میخواهید قابلیت اضافه کردن دسته بندی بدون پاک کردن قبلی را داشته باشید، منطق پیچیده تری نیاز است.
        if category_objs:
            instance.categories.set(category_objs)

        # سپس، بقیه فیلدهای معمولی را در instance به روز میکنیم.
        # از super().update() استفاده نمیکنیم چون میخواهیم منطق اختصاصی خودمان را برای فیلدهای رابطه ای اعمال کنیم.
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        # در نهایت، نمونه به روز شده را ذخیره و برمیگردانیم.
        instance.save()

        return instance




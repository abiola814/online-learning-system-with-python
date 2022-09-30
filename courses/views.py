from django.shortcuts import render
from django.contrib.auth import authenticate, login 
from django.contrib.auth.models import User
from django.contrib.auth import login as lg 
from django.http import HttpResponse
from django.shortcuts import render
from django.views.generic.list import ListView
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404, redirect
from django.views.generic.base import TemplateResponseMixin, View
from django.views.generic.list import ListView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.detail import DetailView
from .models import Course
from .models import Department, Course, Module, Content
from django.contrib.auth.mixins import LoginRequiredMixin,PermissionRequiredMixin
from braces.views import CsrfExemptMixin, JsonRequestResponseMixin
from django.views.generic.base import TemplateResponseMixin,View
from .forms import ModuleFormset
from django.apps import apps
from django.forms.models import modelform_factory
from django.db.models import Count
from .models import Department
#from students.forms import CourseEnrollForm

# Create your views here.

def login(request):
    if request.method=="POST":
        username=request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request,username=username,password=password)
        if user is not None:
            if user.is_active:
                lg(request,user)
                return HttpResponse('Authenticated ''successfully')
        else:
            return render(request,"registration/login.html",{"message":"invalid password or username"})
    return render(request,"registration/login.html")


def signup(request):
    if request.method=="POST":
        name = request.POST.get('name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        passwords = request.POST.get('passwords')
        if User.objects.filter(username=name):
            message='username already exist'
        elif password==passwords:
            user = User.objects.create_user(username=name,email=email,password=passwords)
            user.save()
            return render(request,"registration/login.html")
        elif password != passwords:
            message="password is not the same"
        return render(request,"registration/register.html",{'message': message})
    return render(request,"registration/register.html")

# retrieving data of a particular user
class OwnerMixin(object):
    def get_queryset(self):
        qs = super(OwnerMixin, self).get_queryset()
        return qs.filter(owner=self.request.user)

#validating form mixin 
class OwnerEditMixin(object):
    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super(OwnerEditMixin, self).form_valid(form)

#crating field 
class OwnerCourseMixin(OwnerMixin):
    model = Course
    fields = ['department', 'title', 'slug', 'overview']
    success_url = reverse_lazy('manage_course_list')


class CourseListView(TemplateResponseMixin, View):
	model = Course
	template_name = 'courses/course/list.html'
	def get(self, request, department=None):
		departments = Department.objects.annotate(
		total_courses=Count('courses'))
		courses = Course.objects.annotate(
		total_modules=Count('modules'))
		if department:
			department = get_object_or_404(Department, slug=department)
			courses = courses.filter(department=department)
		return self.render_to_response({'department': departments,
		'department': department,
		'courses': courses})

class ContentDeleteView(View):

    def post(self, request, id):
        content = get_object_or_404(Content,
                                    id=id,
                                    module__course__owner=request.user)
        module = content.module
        content.item.delete()
        content.delete()
        return redirect('module_content_list', module.id)

class ModuleContentListView(TemplateResponseMixin, View):
	template_name = 'courses/manage/module/content_list.html'
	def get(self, request, module_id):
		module = get_object_or_404(Module,id=module_id,course__owner=request.user)
		return self.render_to_response({'module': module})


class ContentCreateUpdateView(TemplateResponseMixin, View):
    module = None
    model = None
    obj = None
    template_name = 'courses/manage/content/form.html'

    def get_model(self, model_name):
        if model_name in ['text', 'video', 'image', 'file']:
            return apps.get_model(app_label='courses', model_name=model_name)
        return None

    def get_form(self, model, *args, **kwargs):
        Form = modelform_factory(model,
                                 exclude=['owner', 'order', 'created', 'updated'])
        return Form(*args, **kwargs)

    def dispatch(self, request, module_id, model_name, id=None):
        self.module = get_object_or_404(Module,
                                        id=module_id,
                                        course__owner=request.user)
        self.model = self.get_model(model_name)
        if id:
            self.obj = get_object_or_404(self.model,
                                         id=id,
                                         owner=request.user)
        return super(ContentCreateUpdateView,
                     self).dispatch(request, module_id, model_name, id)

    def get(self, request, module_id, model_name, id=None):
        form = self.get_form(self.model, instance=self.obj)
        return self.render_to_response({'form': form,
                                        'object': self.obj})

    def post(self, request, module_id, model_name, id=None):
        form = self.get_form(self.model,
                             instance=self.obj,
                             data=request.POST,
                             files=request.FILES)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.owner = request.user
            obj.save()
            if not id:
                # new content
                Content.objects.create(module=self.module,
                                       item=obj)
            return redirect('module_content_list', self.module.id)

        return self.render_to_response({'form': form,
                                        'object': self.obj})
                                        
class CourseModuleUpdateView(TemplateResponseMixin,View):
	template_name = 'courses/manage/module/formset.html'
	course = None
	
	def get_formset(self,data=None):
		return ModuleFormset(instance=self.course,data=data)
	
	def dispatch(self,request,pk):
		self.course = get_object_or_404(Course,id =pk,owner= request.user)
		return super().dispatch(request,pk)
	def get(self,request,*args,**kwargs):
		formset = self.get_formset()
		return self.render_to_response({'course':self.course,'formset':formset})
	def post(self,request,*args,**kwargs):
		formset = self.get_formset(data=request.POST)
		if formset.is_valid():
			formset.save()
			return redirect('manage_course_list')
		return self.render_to_response({'course':self.course,'formset':formset})

#class ManageCourseListView(ListView):
#	model = Course
#	template_name = 'courses/manage/course/list.html'
#	def get_queryset(self):
#		qs = super().get_querytset()
#		return qs.filter(owner=self.requst.user)




class OwnerCourseEditMixin(OwnerCourseMixin, OwnerEditMixin):
    template_name = 'courses/manage/course/form.html'


class ManageCourseListView(OwnerCourseMixin, ListView):
    template_name = 'courses/manage/course/list.html'

class CourseCreateView(PermissionRequiredMixin,
                       OwnerCourseEditMixin,
                       CreateView):
    permission_required = 'courses.add_course'


class CourseUpdateView(PermissionRequiredMixin,
                       OwnerCourseEditMixin,
                       UpdateView):
    permission_required = 'courses.change_course'


class CourseDeleteView(PermissionRequiredMixin,
                       OwnerCourseMixin,
                       DeleteView):

    template_name = 'courses/manage/course/delete.html'
    permission_required = 'courses.delete_course'
    
    

class ModuleOrderView(CsrfExemptMixin, JsonRequestResponseMixin, View):

    def post(self, request):
        for id, order in self.request_json.items():
            Module.objects.filter(id=id,
                                  course__owner=request.user).update(order=order)
        return self.render_json_response({'saved': 'OK'})


class ContentOrderView(CsrfExemptMixin, JsonRequestResponseMixin, View):

    def post(self, request):
        for id, order in self.request_json.items():
            Content.objects.filter(id=id,
                                   module__course__owner=request.user).update(order=order)
        return self.render_json_response({'saved': 'OK'})

class CourseDetailView(DetailView):
    model = Course
    template_name = 'courses/course/detail.html'

    def get_context_data(self, **kwargs):
        context = super(CourseDetailView, self).get_context_data(**kwargs)
        context['enroll_form'] = CourseEnrollForm(initial={'course':self.object})
        return context

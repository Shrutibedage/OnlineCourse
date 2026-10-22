
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.models import User
from django.views.decorators.http import require_POST
from django.db.models import Prefetch

from .models import Course, Lesson, Question, Choice, Submission


def index(request):
    courses = Course.objects.all()
    return render(request, 'onlinecourse/index.html', {
        'courses': courses
    })


def course_details(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    return render(
        request,
        'onlinecourse/course_details_bootstrap.html',
        {'course': course}
    )


def exam(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    questions = Question.objects.filter(course=course).prefetch_related('choices')

    return render(request, 'onlinecourse/exam.html', {
        'course': course,
        'questions': questions,
    })


@require_POST
def submit(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    questions = Question.objects.filter(course=course).prefetch_related('choices')

    selected_ids = []
    score = 0
    total = 0
    results = []

    for question in questions:
        total += question.grade
        answer_key = f'question_{question.id}'
        selected_id = request.POST.get(answer_key)

        selected_choice = None
        if selected_id:
            selected_choice = question.choices.filter(id=selected_id).first()

        if selected_choice:
            selected_ids.append(selected_choice.id)

        correct_choice = question.choices.filter(is_correct=True).first()
        is_correct = bool(
            selected_choice and selected_choice.is_correct
        )

        if is_correct:
            score += question.grade

        results.append({
            'question': question,
            'selected_choice': selected_choice,
            'correct_choice': correct_choice,
            'is_correct': is_correct,
        })

    if request.user.is_authenticated:
        user = request.user
    else:
        user, _ = User.objects.get_or_create(username='exam_guest')

    submission = Submission.objects.create(
        user=user,
        course=course,
        score=score,
    )
    submission.choices.set(selected_ids)

    request.session[f'exam_result_{submission.id}'] = {
        'score': score,
        'total': total,
        'results': [
            {
                'question': item['question'].text,
                'selected': (
                    item['selected_choice'].text
                    if item['selected_choice'] else 'Not answered'
                ),
                'correct': (
                    item['correct_choice'].text
                    if item['correct_choice'] else 'No correct answer configured'
                ),
                'is_correct': item['is_correct'],
            }
            for item in results
        ],
    }

    return redirect('show_exam_result', submission_id=submission.id)


def show_exam_result(request, submission_id):
    submission = get_object_or_404(Submission, id=submission_id)

    # Only show the guest user's results to visitors who submitted them.
    if request.user.is_authenticated:
        if submission.user_id != request.user.id:
            from django.http import HttpResponseForbidden
            return HttpResponseForbidden("You cannot view this exam result.")
    else:
        if submission.user.username != 'exam_guest':
            from django.http import HttpResponseForbidden
            return HttpResponseForbidden("You cannot view this exam result.")

    result_data = request.session.get(f'exam_result_{submission.id}')

    if result_data is None:
        return render(request, 'onlinecourse/result.html', {
            'submission': submission,
            'course': submission.course,
            'score': submission.score,
            'total': None,
            'results': [],
            'congratulations': False,
            'message': 'Detailed exam results are no longer available in this session.',
        })

    score = result_data['score']
    total = result_data['total']

    return render(request, 'onlinecourse/result.html', {
        'submission': submission,
        'course': submission.course,
        'score': score,
        'total': total,
        'results': result_data['results'],
        'congratulations': total > 0 and score == total,
        'message': (
            'Congratulations! You answered all questions correctly!'
            if total > 0 and score == total
            else 'Exam submitted successfully. Review your results below.'
        ),
    })


import os
import json

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required

from openai import OpenAI

from .models import ChatHistory, Quiz, Question


# =========================================================
# AI TUTOR HOME
# =========================================================

def tutor_home(request):

    answer = ""

    if request.method == "POST":

        question = request.POST.get("question", "").strip()

        if question:

            try:

                hf_token = os.getenv("HF_TOKEN")

                if not hf_token:

                    answer = "ERROR: Hugging Face token was not found."

                else:

                    client = OpenAI(
                        base_url="https://router.huggingface.co/v1",
                        api_key=hf_token
                    )

                    messages = [
                        {
                            "role": "system",
                            "content": """
                            You are an advanced AI Tutor for a Smart
                            E-Learning website.

                            You help students learn Python, Django, HTML,
                            CSS, JavaScript, databases and computer science.

                            Explain concepts in simple beginner-friendly
                            language.

                            Give examples whenever useful.

                            If the student asks a follow-up question,
                            understand the previous conversation and answer
                            according to the context.

                            Do not make explanations unnecessarily complicated.
                            """
                        }
                    ]

                    if request.user.is_authenticated:

                        previous_chats = ChatHistory.objects.filter(
                            user=request.user
                        ).order_by('-created_at')[:5]

                        for chat in reversed(previous_chats):

                            messages.append(
                                {
                                    "role": "user",
                                    "content": chat.question
                                }
                            )

                            messages.append(
                                {
                                    "role": "assistant",
                                    "content": chat.answer
                                }
                            )

                    messages.append(
                        {
                            "role": "user",
                            "content": question
                        }
                    )

                    response = client.chat.completions.create(

                        model="openai/gpt-oss-120b:fastest",

                        messages=messages

                    )

                    answer = response.choices[0].message.content

                    if request.user.is_authenticated:

                        ChatHistory.objects.create(
                            user=request.user,
                            question=question,
                            answer=answer
                        )

            except Exception as e:

                answer = "ERROR: " + str(e)

        else:

            answer = "Please enter a question."

    if request.user.is_authenticated:

        history = ChatHistory.objects.filter(
            user=request.user
        ).order_by('-created_at')[:10]

    else:

        history = []

    return render(
        request,
        "tutor/tutor_home.html",
        {
            "answer": answer,
            "history": history
        }
    )


# =========================================================
# CLEAR CHAT HISTORY
# =========================================================

@login_required
def clear_history(request):

    if request.method == "POST":

        ChatHistory.objects.filter(
            user=request.user
        ).delete()

    return redirect('tutor_home')


# =========================================================
# QUIZ LIST
# =========================================================

@login_required
def quiz_list(request):

    quizzes = Quiz.objects.all().order_by('-created_at')

    return render(
        request,
        "tutor/quiz_list.html",
        {
            "quizzes": quizzes
        }
    )


# =========================================================
# ADD QUIZ
# =========================================================

@login_required
def add_quiz(request):

    if request.method == "POST":

        title = request.POST.get(
            "title",
            ""
        ).strip()

        description = request.POST.get(
            "description",
            ""
        ).strip()

        is_ai_generated = (
            request.POST.get("is_ai_generated")
            == "on"
        )

        if title:

            Quiz.objects.create(
                title=title,
                description=description,
                created_by=request.user,
                is_ai_generated=is_ai_generated
            )

            return redirect("quiz_list")

    return render(
        request,
        "tutor/quiz_form.html",
        {
            "page_title": "Add Quiz",
            "button_text": "Add Quiz"
        }
    )


# =========================================================
# EDIT QUIZ
# =========================================================

@login_required
def edit_quiz(request, quiz_id):

    quiz = get_object_or_404(
        Quiz,
        id=quiz_id
    )

    if request.method == "POST":

        quiz.title = request.POST.get(
            "title",
            ""
        ).strip()

        quiz.description = request.POST.get(
            "description",
            ""
        ).strip()

        quiz.is_ai_generated = (
            request.POST.get("is_ai_generated")
            == "on"
        )

        quiz.save()

        return redirect("quiz_list")

    return render(
        request,
        "tutor/quiz_form.html",
        {
            "quiz": quiz,
            "page_title": "Edit Quiz",
            "button_text": "Update Quiz"
        }
    )


# =========================================================
# DELETE QUIZ
# =========================================================

@login_required
def delete_quiz(request, quiz_id):

    quiz = get_object_or_404(
        Quiz,
        id=quiz_id
    )

    if request.method == "POST":

        quiz.delete()

        return redirect("quiz_list")

    return render(
        request,
        "tutor/quiz_confirm_delete.html",
        {
            "quiz": quiz
        }
    )


# =========================================================
# QUESTION LIST
# =========================================================

@login_required
def question_list(request, quiz_id):

    quiz = get_object_or_404(
        Quiz,
        id=quiz_id
    )

    questions = Question.objects.filter(
        quiz=quiz
    ).order_by("id")

    return render(
        request,
        "tutor/question_list.html",
        {
            "quiz": quiz,
            "questions": questions
        }
    )


# =========================================================
# ADD QUESTION
# =========================================================

@login_required
def add_question(request, quiz_id):

    quiz = get_object_or_404(
        Quiz,
        id=quiz_id
    )

    if request.method == "POST":

        question_text = request.POST.get(
            "question_text",
            ""
        ).strip()

        option_a = request.POST.get(
            "option_a",
            ""
        ).strip()

        option_b = request.POST.get(
            "option_b",
            ""
        ).strip()

        option_c = request.POST.get(
            "option_c",
            ""
        ).strip()

        option_d = request.POST.get(
            "option_d",
            ""
        ).strip()

        correct_answer = request.POST.get(
            "correct_answer",
            ""
        )

        if question_text:

            Question.objects.create(
                quiz=quiz,
                question_text=question_text,
                option_a=option_a,
                option_b=option_b,
                option_c=option_c,
                option_d=option_d,
                correct_answer=correct_answer
            )

            return redirect(
                "question_list",
                quiz_id=quiz.id
            )

    return render(
        request,
        "tutor/question_form.html",
        {
            "quiz": quiz,
            "page_title": "Add Question",
            "button_text": "Add Question"
        }
    )


# =========================================================
# EDIT QUESTION
# =========================================================

@login_required
def edit_question(request, question_id):

    question = get_object_or_404(
        Question,
        id=question_id
    )

    if request.method == "POST":

        question.question_text = request.POST.get(
            "question_text",
            ""
        ).strip()

        question.option_a = request.POST.get(
            "option_a",
            ""
        ).strip()

        question.option_b = request.POST.get(
            "option_b",
            ""
        ).strip()

        question.option_c = request.POST.get(
            "option_c",
            ""
        ).strip()

        question.option_d = request.POST.get(
            "option_d",
            ""
        ).strip()

        question.correct_answer = request.POST.get(
            "correct_answer",
            ""
        )

        question.save()

        return redirect(
            "question_list",
            quiz_id=question.quiz.id
        )

    return render(
        request,
        "tutor/question_form.html",
        {
            "quiz": question.quiz,
            "question": question,
            "page_title": "Edit Question",
            "button_text": "Update Question"
        }
    )


# =========================================================
# DELETE QUESTION
# =========================================================

@login_required
def delete_question(request, question_id):

    question = get_object_or_404(
        Question,
        id=question_id
    )

    quiz = question.quiz

    if request.method == "POST":

        question.delete()

        return redirect(
            "question_list",
            quiz_id=quiz.id
        )

    return render(
        request,
        "tutor/question_confirm_delete.html",
        {
            "question": question,
            "quiz": quiz
        }
    )


# =========================================================
# AI QUIZ GENERATOR
# =========================================================

@login_required
def generate_ai_quiz(request):

    if request.method == "POST":

        topic = request.POST.get(
            "topic",
            ""
        ).strip()

        number_of_questions = request.POST.get(
            "number_of_questions",
            "5"
        ).strip()

        if not topic:

            return render(
                request,
                "tutor/ai_quiz_form.html",
                {
                    "error": "Please enter a topic."
                }
            )

        try:

            number_of_questions = int(
                number_of_questions
            )

        except ValueError:

            number_of_questions = 5

        if number_of_questions < 1:

            number_of_questions = 1

        if number_of_questions > 20:

            number_of_questions = 20


        try:

            hf_token = os.getenv("HF_TOKEN")

            if not hf_token:

                return render(
                    request,
                    "tutor/ai_quiz_form.html",
                    {
                        "error": "Hugging Face token was not found."
                    }
                )


            client = OpenAI(

                base_url="https://router.huggingface.co/v1",

                api_key=hf_token

            )


            prompt = f"""
Generate exactly {number_of_questions} multiple choice
questions about {topic}.

Return ONLY valid JSON.

Use this exact format:

[
    {{
        "question": "Question text",
        "option_a": "Option A",
        "option_b": "Option B",
        "option_c": "Option C",
        "option_d": "Option D",
        "correct_answer": "A"
    }}
]

Rules:

1. Generate exactly {number_of_questions} questions.
2. Every question must have exactly four options.
3. correct_answer must contain only A, B, C, or D.
4. Questions should be educational and suitable for students.
5. Do not add explanations.
6. Do not add markdown.
7. Return only JSON.
"""


            response = client.chat.completions.create(

                model="openai/gpt-oss-120b:fastest",

                messages=[

                    {
                        "role": "system",
                        "content": "You are an AI quiz generator."
                    },

                    {
                        "role": "user",
                        "content": prompt
                    }

                ]

            )


            ai_response = (
                response
                .choices[0]
                .message
                .content
            )


            ai_response = ai_response.strip()


            if ai_response.startswith("```"):

                ai_response = (
                    ai_response
                    .replace("```json", "")
                    .replace("```", "")
                    .strip()
                )


            questions_data = json.loads(
                ai_response
            )


            quiz = Quiz.objects.create(

                title=f"AI Quiz - {topic}",

                description=(
                    f"AI generated quiz about {topic}."
                ),

                created_by=request.user,

                is_ai_generated=True

            )


            for item in questions_data:

                Question.objects.create(

                    quiz=quiz,

                    question_text=item["question"],

                    option_a=item["option_a"],

                    option_b=item["option_b"],

                    option_c=item["option_c"],

                    option_d=item["option_d"],

                    correct_answer=item["correct_answer"]

                )


            return redirect(
                "question_list",
                quiz_id=quiz.id
            )


        except Exception as e:

            return render(

                request,

                "tutor/ai_quiz_form.html",

                {
                    "error": "AI Quiz Generation Failed: " + str(e)
                }

            )


    return render(

        request,

        "tutor/ai_quiz_form.html"

    )
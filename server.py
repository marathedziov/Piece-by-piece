import os
import random

from pprint import pprint
import json

from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

from flask import Flask, render_template, redirect, request, session, make_response
from data import db_session
from data.users import User
from forms.user import RegisterForm, LoginForm
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from data.animals import Animal
from data.ModeOne import ModeOne
from data.ModeTwo import ModeTwo


# Base.metadata.create_all(engine)


class Task:
    def __init__(self):
        session["current_question"] = 0
        session["count_wrong_answer"] = 0
        session["mode_value"] = 0
        session["user_points_mode1"] = 100
        session["user_points_mode2"] = 100
        session["current_hint"] = 0
        session["btn_hint_text"] = "Подсказка"
        session["hint_text"] = ""
        session["lst_tasks"] = []
        session["lst_imgs"] = []

    def get_random_id(self):

        mode_value = session.get("mode_value", 1)
        print(mode_value)
        if mode_value in [1, 2]:
            session_db = db_session.create_session()
            query = session_db.query(Animal.id).filter(Animal.mode == mode_value).all()
            session_db.close()
            ides = [animal.id for animal in query]
            if ides:
                random_id = random.choice(ides)
                session["random_id"] = random_id

    def get_tasks_by_random_id(self):
        print("Getting tasks by random")
        mode_value = session.get("mode_value", 1)
        random_id = session.get("random_id", 1)

        if mode_value == 1:
            session_db = db_session.create_session()
            query_tasks = session_db.query(ModeOne).filter(ModeOne.id_animal == random_id).all()
            session_db.close()
            lst_tasks = list()
            for i_task in query_tasks:
                lst_task = [i_task.tasks, i_task.answers, i_task.png]
                lst_tasks.append(lst_task)
            random.shuffle(lst_tasks)
            session["lst_tasks"] = json.dumps(lst_tasks)

        elif mode_value == 2:
            session_db = db_session.create_session()

            query_task = session_db.query(ModeTwo).filter(ModeTwo.id_animal == random_id)
            session_db.close()

            lst_tasks = session.get("lst_tasks", [])
            for i_task in query_task:
                lst_task = [i_task.mp3[0], i_task.png[0], i_task.answer[0]]
                lst_tasks.append(lst_task)

            session["lst_tasks"] = json.dumps(lst_tasks)

        # self.texts_by_level()

    def get_name_animal(self):
        session_db = db_session.create_session()

        random_id = session.get("random_id", 1)
        name_animal = session_db.query(Animal.oset_name).filter(Animal.id == random_id).first()
        session_db.close()
        print(name_animal)
        session['name_animal'] = name_animal[0]

    def texts_by_level(self):
        print("texts_by_level")
        mode_value = session.get('mode_value', 1)
        current_question = session.get('current_question', 1)
        lst_tasks = json.loads(session.get('lst_tasks', []))
        random_id = session.get('random_id', 1)

        if current_question < len(lst_tasks):
            if mode_value == 1:
                list_random_wrong_words = []
                while len(list_random_wrong_words) < 3:
                    random_index = random.choice(range(len(lst_tasks)))
                    if random_index != current_question and random_index not in list_random_wrong_words:
                        list_random_wrong_words.append(random_index)
                list_button_text_mode1 = [lst_tasks[current_question][1],
                                          lst_tasks[list_random_wrong_words[0]][1],
                                          lst_tasks[list_random_wrong_words[1]][1],
                                          lst_tasks[list_random_wrong_words[2]][1]]
                print("texts_by_level", list_button_text_mode1)
                print(lst_tasks[current_question][1])
                random.shuffle(list_button_text_mode1)
                session["list_button_text_mode1"] = json.dumps(list_button_text_mode1)
            elif mode_value == 2:
                pass
                # Session_db = sessionmaker(bind=engine)
                # session_db = Session_db()
                #
                # query = session_db.query(Animal.shape_used).filter(Animal.id == random_id)
                # list_button_img_mode2 = [animal[0] for animal in query.all()][0].split(', ')
                # session_db.close()
                #
                # res = make_response()
                # res.set_cookie('list_button_img_mode2', json.dumps(list_button_img_mode2))
                # res.set_cookie('audio', str(lst_tasks[task.correct_question][0]))

    def restart_level(self):
        session["current_question"] = 0
        session["lst_imgs"] = json.dumps([])

    def update_level(self):
        session["user_points_mode1"] = 100
        session["user_points_mode2"] = 100
        session["current_hint"] = 0

        self.restart_level()
        self.texts_by_level()

    def get_all_from_task(self):
        print("get_all_from_task")
        task.get_random_id()
        task.get_tasks_by_random_id()
        task.get_name_animal()

    def check_answer_animal(self, user_input):
        print("check_answer_animal!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        name_animal = session.get('name_animal')
        user_points_mode1 = session.get('user_points_mode1')
        if user_input.lower().strip() == name_animal:
            print("daaaaaaaaaaaaaaaaaa")
            db_sess = db_session.create_session()
            user = db_sess.query(User).filter(User.id == current_user.id).first()
            user.user_points_mode1 += user_points_mode1
            db_sess.commit()
            return True


app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@app.route('/')
@app.route('/index')
def index():
    global task
    task = Task()
    return render_template('main_window.html')


@app.route('/rules')
def rules():
    return render_template('rules.html')


@app.route('/register', methods=['GET', 'POST'])
def reqister():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Пароли не совпадают")
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.name == form.name.data).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Пользователь с таким именем уже есть")
        user = User(
            name=form.name.data,
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        login_user(user)
        return redirect('/select_level')
    return render_template('register.html', title='Регистрация', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.name == form.name.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/select_level")
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form)
    return render_template('login.html', title='Авторизация', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


@app.route('/select_level', methods=['GET', 'POST'])
def select_level():
    print("select_level")
    if request.method == 'POST':
        selected_mode = request.form.get('btn')

        if selected_mode == "1":
            session['mode_value'] = 1
            task.get_all_from_task()
            task.update_level()
            # return redirect("/update_level_one")
            return redirect("/mode_one")
        elif selected_mode == "2":
            session['mode_value'] = 1
            return redirect("/update_level_two")

    return render_template('select_level.html')


@app.route('/update_level_one')
def update_level_one():
    global task
    task.get_all_from_task()
    print('Update level one')
    task.update_level()
    print('Update level')
    return redirect("/mode_one")


@app.route('/mode_one', methods=['GET', 'POST'])
def mode_one():
    print("event mode one")
    current_question = session.get('current_question')
    print("mode_one current_question", current_question)

    lst_tasks = json.loads(session.get('lst_tasks', ''))
    lst_imgs = json.loads(session.get('lst_imgs', ''))
    count_wrong_answer = session.get('count_wrong_answer')
    name_animal = session.get('name_animal')
    user_points_mode1 = session.get('user_points_mode1')
    current_hint = session.get('current_hint')
    list_button_text_mode1 = json.loads(session.get('list_button_text_mode1'))
    print("mode_one", list_button_text_mode1)
    print(lst_tasks)
    print("mode_one current_question", current_question)
    if current_question < len(lst_tasks):
        question = lst_tasks[current_question][0]
        print(question)

    hint_text = session.get('hint_text')
    btn_hint_text = session.get('btn_hint_text')

    if request.method == 'POST':
        print('POst')

        selected_answer = request.form.get('btn')
        print("selected_answer", selected_answer)
        btn_answer = request.form.get('answer')
        btn_hint = request.form.get('hint')
        print("btn click", btn_answer, btn_hint)

        if current_question == len(lst_tasks):
            user_input = request.form.get('animal')
            flag_animal = task.check_answer_animal(user_input)
            if flag_animal:
                return redirect("/select_level")
            else:
                user_points_mode1 -= 5
                session["user_points_mode1"] = user_points_mode1

        elif selected_answer == lst_tasks[current_question][1]:
            current_question += 1
            lst_imgs.append(lst_tasks[current_question - 1][2])
            session["lst_imgs"] = json.dumps(lst_imgs)
            count_wrong_answer = 0
            session["count_wrong_answer"] = count_wrong_answer
            session["current_question"] = current_question
            task.texts_by_level()

        else:
            count_wrong_answer += 1
            user_points_mode1 -= 5
            session["count_wrong_answer"] = count_wrong_answer
            if count_wrong_answer == 2:
                user_points_mode1 -= 5
                count_wrong_answer = 0
                session["user_points_mode1"] = user_points_mode1
                session["count_wrong_answer"] = count_wrong_answer
                task.restart_level()
                task.texts_by_level()
            if user_points_mode1 < 0:
                user_points_mode1 = 0
            session["user_points_mode1"] = user_points_mode1

        list_button_text_mode1 = json.loads(session.get('list_button_text_mode1'))
        if current_question < len(lst_tasks):
            question = lst_tasks[current_question][0]
        print("Post", list_button_text_mode1)

        if btn_hint is not None:
            current_hint = session.get('current_hint')
            name_animal = session.get('name_animal')
            current_hint += 1
            session["current_hint"] = current_hint
            print('подсказка по счету', current_hint)
            btn_hint_text = "Подсказка"
            hint_text = ""
            if current_hint == 1:
                hint_text = f"Букв в слове: {len(str(name_animal))}"
                user_points_mode1 -= 10
                btn_hint_text = "Подсказка"
            elif current_hint == 2:
                hint_text = f"Первая буква: {name_animal[0]}"
                user_points_mode1 -= 10
                btn_hint_text = "Сдаюсь"
            elif current_hint >= 3:
                hint_text = f"Правильный ответ: {name_animal}"
                user_points_mode1 = 0
            if user_points_mode1 < 0:
                user_points_mode1 = 0

            print("подсказка", hint_text)
            session["hint_text"] = hint_text
            session["user_points_mode1"] = user_points_mode1
            session["btn_hint_text"] = btn_hint_text

            t = session.get('list_button_text_mode1', '')
            print(t)
            list_button_text_mode1 = json.loads(session.get('list_button_text_mode1', []))
            lst_imgs = json.loads(session.get('lst_imgs', []))
            current_question = session.get('current_question', 1)
            lst_tasks = json.loads(session.get('lst_tasks', []))
            if current_question < len(lst_tasks):
                question = lst_tasks[current_question][0]
            else:
                question = ""

            return render_template('mode_one.html', question=question,
                                   btn_texts=list_button_text_mode1, file_imgs=lst_imgs,
                                   user_points=user_points_mode1, correct_question=current_question,
                                   len_lst_tasks=len(lst_tasks), name_animal=name_animal,
                                   curent_hint=current_hint, hint_text=hint_text,
                                   btn_hint_text=btn_hint_text)

    if request.method == 'GET':
        print('Get')
        user_input = request.args.get('animal')

        if user_input is not None:
            flag_animal = task.check_answer_animal(user_input)
            if flag_animal:
                return redirect("/select_level")
            else:
                user_points_mode1 -= 5
                session["user_points_mode1"] = user_points_mode1

        else:
            user_points_mode1 -= 5
            if user_points_mode1 < 0:
                user_points_mode1 = 0
            session["user_points_mode1"] = user_points_mode1

    try:
        question = lst_tasks[current_question][0]
    except Exception as e:
        question = e
    print("render")
    return render_template('mode_one.html', question=question,
                           btn_texts=list_button_text_mode1, file_imgs=lst_imgs,
                           user_points=user_points_mode1, correct_question=current_question,
                           len_lst_tasks=len(lst_tasks), name_animal=name_animal,
                           curent_hint=current_hint, hint_text=hint_text,
                           btn_hint_text=btn_hint_text)


@app.route('/mode_two', methods=['GET', 'POST'])
def mode_two():
    if request.method == 'POST':
        selected_answer = request.form.get('btn')

        lst_tasks = eval(request.cookies.get('lst_tasks'))
        correct_question = int(request.cookies.get('correct_question'))
        lst_tasks = eval(request.cookies.get('lst_tasks'))
        lst_imgs = eval(request.cookies.get('lst_imgs'))
        count_wrong_answer = int(request.cookies.get('count_wrong_answer'))
        user_points_mode2 = int(request.cookies.get('user_points_mode2'))

        if selected_answer == lst_tasks[correct_question][2]:
            correct_question += 1
            lst_imgs.append(lst_tasks[correct_question - 1][1])
            count_wrong_answer = 0
            task.texts_by_level()

        else:
            count_wrong_answer += 1
            user_points_mode2 -= 5
            if count_wrong_answer == 2:
                user_points_mode2 -= 5
                count_wrong_answer = 0
                task.restart_level()
                task.texts_by_level()
            if user_points_mode2 < 0:
                user_points_mode2 = 0
        response = make_response()
        response.set_cookie('correct_question', str(correct_question))
        response.set_cookie('lst_imgs', str(lst_imgs))
        response.set_cookie('count_wrong_answer', str(count_wrong_answer))
        response.set_cookie('user_points_mode2', str(user_points_mode2))

    if request.method == 'GET':
        user_input = request.args.get('animal')

        name_animal = request.cookies.get('name_animal')
        user_points_mode2 = int(request.cookies.get('user_points_mode2'))

        if user_input is not None:
            if user_input.lower().strip() == name_animal:
                db_sess = db_session.create_session()
                user = db_sess.query(User).filter(User.id == current_user.id).first()
                user.user_points_mode2 += user_points_mode2
                db_sess.commit()

                return redirect("/select_level")
            else:
                user_points_mode2 -= 5
                if user_points_mode2 < 0:
                    user_points_mode2 = 0
                response = make_response()
                response.set_cookie('user_points_mode2', str(user_points_mode2))

        else:

            current_hint = int(request.cookies.get('current_hint'))
            name_animal = request.cookies.get('name_animal')
            if curent_hint == 1:
                hint_text = f"Букв в слове: {len(str(name_animal))}"
                user_points_mode2 -= 10
                btn_hint_text = "Подсказка"
            elif current_hint == 2:
                hint_text = f"Первая буква: {name_animal[0]}"
                user_points_mode2 -= 10
                btn_hint_text = "Сдаюсь"
            elif current_hint >= 3:
                hint_text = f"Правильный ответ: {name_animal}"
                user_points_mode2 = 0
            else:
                hint_text = ""
                btn_hint_text = "Подсказка"
            if user_points_mode2 < 0:
                user_points_mode2 = 0
            current_hint += 1

            response.set_cookie('hint_text', str(hint_text))
            response.set_cookie('user_points_mode2', str(user_points_mode2))
            response.set_cookie('btn_hint_text', str(btn_hint_text))

            list_button_img_mode2 = eval(request.cookies.get('list_button_img_mode2'))
            lst_imgs = eval(request.cookies.get('lst_imgs'))
            correct_question = int(request.cookies.get('correct_question'))
            lst_tasks = eval(request.cookies.get('lst_tasks'))
            audio = request.cookies.get('audio')

            return render_template('mode_two.html', question="Послушай диктора и выбери названную им фигуру",
                                   btn_imges=list_button_img_mode2, file_imgs=lst_imgs,
                                   user_points=user_points_mode2, correct_audio=audio,
                                   correct_question=correct_question,
                                   len_lst_tasks=len(lst_tasks), name_animal=name_animal,
                                   curent_hint=current_hint, hint_text=hint_text,
                                   btn_hint_text=btn_hint_text)

    list_button_img_mode2 = eval(request.cookies.get('list_button_img_mode2'))
    lst_imgs = eval(request.cookies.get('lst_imgs'))
    user_points_mode2 = int(request.cookies.get('user_points_mode2'))
    audio = request.cookies.get('audio')
    correct_question = int(request.cookies.get('correct_question'))
    lst_tasks = eval(request.cookies.get('lst_tasks'))
    name_animal = request.cookies.get('name_animal')
    current_hint = int(request.cookies.get('current_hint'))
    hint_text = request.cookies.get('hint_text')
    btn_hint_text = request.cookies.get('btn_hint_text')

    return render_template('mode_two.html', question="Послушай диктора и выбери названную им фигуру",
                           btn_imges=list_button_img_mode2, file_imgs=lst_imgs,
                           user_points=user_points_mode2, correct_audio=audio,
                           correct_question=correct_question,
                           len_lst_tasks=len(lst_tasks), name_animal=name_animal,
                           curent_hint=current_hint, hint_text=hint_text,
                           btn_hint_text=btn_hint_text)


@app.route('/leader_board')
def leader_board():
    db_sess = db_session.create_session()
    users = db_sess.query(User).all()

    user_points = [(user.user_points_mode1 + user.user_points_mode2, user) for user in users]

    sorted_users = sorted(user_points, key=lambda x: x[0], reverse=True)

    enumerated_users = [(index + 1, user) for index, (_, user) in enumerate(sorted_users)]
    print(enumerated_users)
    return render_template('leader_board.html', users=enumerated_users)


@app.route('/update_level_two')
def update_level_two():
    lst_tasks = []
    mode_value = 2
    response = make_response()
    response.set_cookie('lst_tasks', str(lst_tasks))
    response.set_cookie('mode_value', str(mode_value))

    task.get_all_from_task()

    task.update_level()
    return redirect("/mode_two")


if __name__ == '__main__':
    db_session.global_init("db/DataBase.db")

    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

import os
import random
import json

from flask import Flask, render_template, redirect, request, session
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.utils import secure_filename

from data import db_session
from data.users import User
from data.animals import Animal
from data.ModeOne import ModeOne
from data.ModeTwo import ModeTwo
from data.ModeAdditional import ModeAdditional
from forms.user import RegisterForm, LoginForm, LevelForm


class Task:
    def __init__(self):
        session["current_question"] = 0
        session["count_wrong_answer"] = 0
        session["mode_value"] = 0
        session["user_points_mode1"] = 105
        session["user_points_mode2"] = 105
        session["current_hint"] = 0
        session["btn_hint_text"] = "Подсказка"
        session["hint_text"] = ""
        session["lst_tasks"] = []
        session["lst_imgs"] = []

    def get_random_id(self):
        mode_value = session.get("mode_value", 1)
        if mode_value in [1, 2]:
            session_db = db_session.create_session()
            query = session_db.query(Animal.id).filter(Animal.mode == mode_value).all()
            session_db.close()
            ides = [animal.id for animal in query]
            if ides:
                random_id = random.choice(ides)
                session["random_id"] = random_id

    def get_tasks_by_random_id(self):
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

            lst_tasks = list()
            for i_task in query_task:
                lst_task = [i_task.mp3, i_task.png, i_task.answer[0]]
                lst_tasks.append(lst_task)
            random.shuffle(lst_tasks)
            session["lst_tasks"] = json.dumps(lst_tasks)

    def get_name_animal(self):
        session_db = db_session.create_session()

        random_id = session.get("random_id", 1)
        name_animal = session_db.query(Animal.oset_name).filter(Animal.id == random_id).first()
        session_db.close()
        session['name_animal'] = name_animal[0]

    def texts_by_level(self):
        mode_value = session.get('mode_value', 1)
        current_question = session.get('current_question', 1)
        lst_tasks = json.loads(session.get('lst_tasks', []))

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
                random.shuffle(list_button_text_mode1)
                session["list_button_text_mode1"] = json.dumps(list_button_text_mode1)
            elif mode_value == 2:
                random_id = session.get('random_id')
                session_db = db_session.create_session()

                query = session_db.query(Animal.shape_used).filter(Animal.id == random_id)
                list_button_img_mode2 = [animal[0] for animal in query.all()][0].split(', ')
                session_db.close()

                session["list_button_img_mode2"] = json.dumps(list_button_img_mode2)
                session["audio"] = lst_tasks[current_question][0]

    def restart_level(self):
        session["current_question"] = 0
        session["lst_imgs"] = json.dumps([])

    def update_level(self):
        session["user_points_mode1"] = 105
        session["user_points_mode2"] = 105

        session["btn_hint_text"] = "Подсказка"
        session["hint_text"] = ""

        session["current_hint"] = 0

        self.restart_level()
        self.texts_by_level()

    def get_all_from_task(self):
        task.get_random_id()
        task.get_tasks_by_random_id()
        task.get_name_animal()

    def check_answer_animal(self, user_input):
        name_animal = session.get('name_animal')
        user_points_mode1 = session.get('user_points_mode1')
        user_points_mode2 = session.get('user_points_mode2')
        mode_value = session.get('mode_value')
        if user_input.lower().strip() == name_animal:
            db_sess = db_session.create_session()
            user = db_sess.query(User).filter(User.id == current_user.id).first()
            if mode_value == 1:
                user.user_points_mode1 += user_points_mode1
            elif mode_value == 2:
                user.user_points_mode2 += user_points_mode2
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
            user_type=form.user_type.data
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
    if request.method == 'POST':
        selected_mode = request.form.get('btn')

        if selected_mode == "1":
            session['mode_value'] = 1
            task.get_all_from_task()
            task.update_level()
            return redirect("/mode_one")
        elif selected_mode == "2":
            session['mode_value'] = 2
            task.get_all_from_task()
            task.update_level()
            return redirect("/mode_two")
        elif selected_mode == "0":
            return redirect("/additional_mode")

    return render_template('select_level.html')


@app.route('/mode_one', methods=['GET', 'POST'])
def mode_one():
    current_question = session.get('current_question')

    lst_tasks = json.loads(session.get('lst_tasks', []))
    lst_imgs = json.loads(session.get('lst_imgs', []))
    count_wrong_answer = session.get('count_wrong_answer')
    name_animal = session.get('name_animal')
    user_points_mode1 = session.get('user_points_mode1')
    current_hint = session.get('current_hint')
    list_button_text_mode1 = json.loads(session.get('list_button_text_mode1'))
    if current_question < len(lst_tasks):
        question = lst_tasks[current_question][0]

    hint_text = session.get('hint_text')
    btn_hint_text = session.get('btn_hint_text')

    if request.method == 'POST':
        selected_answer = request.form.get('btn')
        btn_answer = request.form.get('answer')
        btn_hint = request.form.get('hint')

        if current_question == len(lst_tasks):
            user_input = request.form.get('animal')
            flag_animal = task.check_answer_animal(user_input)
            if flag_animal:
                return redirect("/select_level")
            else:
                user_points_mode1 -= 5
                if user_points_mode1 < 0:
                    user_points_mode1 = 0
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

        if btn_hint is not None:
            current_hint = session.get('current_hint')
            name_animal = session.get('name_animal')
            current_hint += 1
            session["current_hint"] = current_hint
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

            session["hint_text"] = hint_text
            session["user_points_mode1"] = user_points_mode1
            session["btn_hint_text"] = btn_hint_text

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
    return render_template('mode_one.html', question=question,
                           btn_texts=list_button_text_mode1, file_imgs=lst_imgs,
                           user_points=user_points_mode1, correct_question=current_question,
                           len_lst_tasks=len(lst_tasks), name_animal=name_animal,
                           curent_hint=current_hint, hint_text=hint_text,
                           btn_hint_text=btn_hint_text)


@app.route('/mode_two', methods=['GET', 'POST'])
def mode_two():
    current_question = session.get('current_question')
    lst_tasks = json.loads(session.get('lst_tasks', []))
    lst_imgs = json.loads(session.get('lst_imgs', []))
    user_points_mode2 = session.get('user_points_mode2')
    count_wrong_answer = session.get('count_wrong_answer')

    if request.method == 'POST':
        selected_answer = request.form.get('btn')
        btn_answer = request.form.get('answer')
        btn_hint = request.form.get('hint')

        if current_question == len(lst_tasks):
            user_input = request.form.get('animal')
            flag_animal = task.check_answer_animal(user_input)
            if flag_animal:
                return redirect("/select_level")
            else:
                user_points_mode2 -= 5
                if user_points_mode2 < 0:
                    user_points_mode2 = 0
                session["user_points_mode2"] = user_points_mode2

        elif selected_answer == lst_tasks[current_question][2]:
            current_question += 1
            lst_imgs.append(lst_tasks[current_question - 1][1])
            session["lst_imgs"] = json.dumps(lst_imgs)
            count_wrong_answer = 0
            session["count_wrong_answer"] = count_wrong_answer
            session["current_question"] = current_question

            task.texts_by_level()

        else:
            count_wrong_answer += 1
            user_points_mode2 -= 5
            session["count_wrong_answer"] = count_wrong_answer
            if count_wrong_answer == 2:
                user_points_mode2 -= 5
                count_wrong_answer = 0
                session["user_points_mode2"] = user_points_mode2
                session["count_wrong_answer"] = count_wrong_answer
                task.restart_level()
                task.texts_by_level()
            if user_points_mode2 < 0:
                user_points_mode2 = 0
            session["user_points_mode2"] = user_points_mode2

        btn_hint_text = "Подсказка"
        hint_text = ""
        if btn_hint is not None:
            current_hint = session.get('current_hint')
            name_animal = session.get('name_animal')
            current_hint += 1
            session["current_hint"] = current_hint

            if current_hint == 1:
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
            if user_points_mode2 < 0:
                user_points_mode2 = 0

            session["hint_text"] = hint_text
            session["user_points_mode2"] = user_points_mode2
            session["btn_hint_text"] = btn_hint_text

            list_button_text_mode1 = json.loads(session.get('list_button_text_mode1', []))
            lst_imgs = json.loads(session.get('lst_imgs', []))
            current_question = session.get('current_question', 1)
            lst_tasks = json.loads(session.get('lst_tasks', []))
            if current_question < len(lst_tasks):
                question = lst_tasks[current_question][0]
            else:
                question = ""
            list_button_img_mode2 = session.get('list_button_img_mode2')
            audio = session.get('audio')
            return render_template('mode_two.html', question="Послушай диктора и выбери названную им фигуру",
                                   btn_imges=list_button_img_mode2, file_imgs=lst_imgs,
                                   user_points=user_points_mode2, correct_audio=audio,
                                   correct_question=current_question,
                                   len_lst_tasks=len(lst_tasks), name_animal=name_animal,
                                   curent_hint=current_hint, hint_text=hint_text,
                                   btn_hint_text=btn_hint_text)

    if request.method == 'GET':
        user_input = request.args.get('animal')

        if user_input is not None:
            flag_animal = task.check_answer_animal(user_input)
            if flag_animal:
                return redirect("/select_level")
            else:
                user_points_mode2 -= 5
                session["user_points_mode2"] = user_points_mode2
        else:
            user_points_mode2 -= 5
            if user_points_mode2 < 0:
                user_points_mode2 = 0
            session["user_points_mode2"] = user_points_mode2

        name_animal = session.get('name_animal')
        user_points_mode2 = int(session.get('user_points_mode2'))
        current_hint = int(session.get('current_hint'))
        btn_hint_text = session.get('btn_hint_text')
        hint_text = session.get('hint_text')
        list_button_img_mode2 = json.loads(session.get('list_button_img_mode2'))
        lst_imgs = json.loads(session.get('lst_imgs'))
        current_question = int(session.get('current_question'))
        lst_tasks = json.loads(session.get('lst_tasks'))
        audio = session.get('audio')

        print(audio)
        print(lst_imgs)
        return render_template('mode_two.html', question="Послушай диктора и выбери названную им фигуру",
                               btn_imges=list_button_img_mode2, file_imgs=lst_imgs,
                               user_points=user_points_mode2, correct_audio=audio,
                               correct_question=current_question,
                               len_lst_tasks=len(lst_tasks), name_animal=name_animal,
                               curent_hint=current_hint, hint_text=hint_text,
                               btn_hint_text=btn_hint_text)

    name_animal = session.get('name_animal')
    user_points_mode2 = int(session.get('user_points_mode2'))
    current_hint = int(session.get('current_hint'))
    btn_hint_text = session.get('btn_hint_text')
    hint_text = session.get('hint_text')
    list_button_img_mode2 = json.loads(session.get('list_button_img_mode2'))
    lst_imgs = json.loads(session.get('lst_imgs'))
    current_question = int(session.get('current_question'))
    lst_tasks = json.loads(session.get('lst_tasks'))
    audio = session.get('audio')

    print(audio)
    print(lst_imgs)
    return render_template('mode_two.html', question="Послушай диктора и выбери названную им фигуру",
                           btn_imges=list_button_img_mode2, file_imgs=lst_imgs,
                           user_points=user_points_mode2, correct_audio=audio,
                           correct_question=current_question,
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
    return render_template('leader_board.html', users=enumerated_users)


@app.route('/additional_mode')
def additional_mode():
    db_sess = db_session.create_session()
    role = db_sess.query(User).filter(User.name == current_user.name).first().user_type
    role = False if role == "ученик" else True
    return render_template('additional_mode.html', teacher=role)


@app.route('/editor', methods=['GET', 'POST'])
def editor():
    form = LevelForm()
    levels_data = []
    if request.method == 'POST':
        level_name = form.level_name.data
        level_oset_name = form.level_oset_name.data
        for i, level in enumerate(form.levels.entries):
            word = level.word.data
            translation = level.translation.data
            image = level.image.data

            levels_data.append((i + 1, {
                'level_name': level_name,
                'tasks': word,
                'answers': translation,
                'png': secure_filename(image.filename)
            }))

            db_sess = db_session.create_session()

            if i == 0:
                animal = Animal(
                    mode=3,
                    name=level_name,
                    oset_name=level_oset_name
                )
                db_sess.add(animal)
                db_sess.commit()

            id = db_sess.query(Animal.id).filter(Animal.name == level_name).all()

            level = ModeAdditional(
                id_animal=id,
                tasks=word,
                answers=translation,
                png=secure_filename(image.filename)
            )

            db_sess.add(level)
            db_sess.commit()

        levels_data.clear()
        return redirect('/additional_mode')

    return render_template('editor.html', form=form, levels_data=levels_data)


if __name__ == '__main__':
    db_session.global_init("db/DataBase.db")

    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

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

engine = create_engine('sqlite:///db/DataBase.db', echo=False)
Base = declarative_base()


class Animal(Base):
    __tablename__ = 'animals'
    id = Column(Integer, primary_key=True)
    mode = Column(String)
    name = Column(String)
    oset_name = Column(String)
    shape_used = Column(String)

    mode_one = relationship("ModeOne", back_populates="animal")


class ModeOne(Base):
    __tablename__ = 'mode_one'
    id = Column(Integer, primary_key=True)
    id_animal = Column(Integer, ForeignKey('animals.id'))
    tasks = Column(String)
    answers = Column(String)
    png = Column(String)

    animal = relationship("Animal", back_populates="mode_one")


Base.metadata.create_all(engine)


class ModeTwo(Base):
    __tablename__ = 'mode_two'
    id = Column(Integer, primary_key=True)
    id_animal = Column(Integer, ForeignKey('animals.id'))
    mp3 = Column(String)
    png = Column(String)
    answer = Column(String)


Base.metadata.create_all(engine)


class Task:
    def __init__(self):
        res = make_response()
        res.set_cookie("correct_question", '0')
        res.set_cookie("count_wrong_answer", '0')
        res.set_cookie("mode_value", '0')
        res.set_cookie("user_points_mode1", '100')
        res.set_cookie("user_points_mode2", '100')
        res.set_cookie("current_hint", '0')
        res.set_cookie("btn_hint_text", "Подсказка")
        res.set_cookie("flag_hint", 'True')
        res.set_cookie("hint_text", "")
        res.set_cookie("lst_tasks", json.dumps([]))
        res.set_cookie("lst_imgs", json.dumps([]))

    def get_random_id(self):
        Session = sessionmaker(bind=engine)
        session = Session()

        query = session.query(Animal.id).filter(Animal.mode == self.mode_value)
        ides = [animal[0] for animal in query.all()]

        session.close()

        random_id = random.choice(ides)
        res = make_response()
        res.set_cookie("random_id", str(random_id))

    def get_tasks_by_random_id(self):

        mode_value = int(request.cookies.get('ides_cookie'))
        random_id = int(request.cookies.get('random_id'))

        if mode_value == 1:
            Session = sessionmaker(bind=engine)
            session = Session()

            query_tasks = session.query(ModeOne.tasks).filter(ModeOne.id_animal == random_id)
            query_pnges = session.query(ModeOne.answers).filter(ModeOne.id_animal == random_id)
            query_pngs = session.query(ModeOne.png).filter(ModeOne.id_animal == random_id)

            for task, answer, png in zip(query_tasks, query_pnges, query_pngs):
                lst_task = [task[0], answer[0], png[0]]

                lst_tasks = eval(request.cookies.get('lst_tasks'))
                lst_tasks.append(lst_task)
                response = make_response()
                response.set_cookie('lst_tasks', str(lst_tasks))
            session.close()

        elif mode_value == 2:
            Session = sessionmaker(bind=engine)
            session = Session()

            query_mp3es = session.query(ModeTwo.mp3).filter(ModeTwo.id_animal == random_id)
            query_pnges = session.query(ModeTwo.png).filter(ModeTwo.id_animal == random_id)
            query_answers = session.query(ModeTwo.answer).filter(ModeTwo.id_animal == random_id)
            for mp3, png, answer in zip(query_mp3es, query_pnges, query_answers):
                lst_task = [mp3[0], png[0], answer[0]]

                lst_tasks = eval(request.cookies.get('lst_tasks'))
                lst_tasks.append(lst_task)
                response = make_response()
                response.set_cookie('lst_tasks', str(lst_tasks))
            session.close()

        lst_tasks = eval(request.cookies.get('lst_tasks'))
        random.shuffle(lst_tasks)
        response = make_response()
        response.set_cookie('lst_tasks', str(lst_tasks))

        self.texts_by_level()

    def get_name_animal(self):
        Session = sessionmaker(bind=engine)
        session = Session()

        random_id = int(request.cookies.get('random_id'))
        name_animal = session.query(Animal.oset_name).filter(Animal.id == random_id).first()
        session.close()

        res = make_response()
        res.set_cookie("name_animal", str(name_animal[0]))

    def texts_by_level(self):
        mode_value = int(request.cookies.get('ides_cookie'))
        correct_question = int(request.cookies.get('correct_question'))
        lst_tasks = eval(request.cookies.get('lst_tasks'))
        random_id = int(request.cookies.get('random_id'))
        if correct_question != len(lst_tasks):
            if mode_value == 1:
                list_random_wrong_words = []
                while len(list_random_wrong_words) < 3:
                    random_index = random.choice(range(len(lst_tasks)))
                    if random_index != correct_question and random_index not in list_random_wrong_words:
                        list_random_wrong_words.append(random_index)

                list_button_text_mode1 = [lst_tasks[correct_question][1],
                                          lst_tasks[list_random_wrong_words[0]][1],
                                          lst_tasks[list_random_wrong_words[1]][1],
                                          lst_tasks[list_random_wrong_words[2]][1]]

                random.shuffle(list_button_text_mode1)
                res = make_response()
                res.set_cookie('list_button_text_mode1', json.dumps(list_button_text_mode1))
                res.set_cookie('question', str(lst_tasks[task.correct_question][0]))
            elif mode_value == 2:
                Session = sessionmaker(bind=engine)
                session = Session()

                query = session.query(Animal.shape_used).filter(Animal.id == random_id)
                list_button_img_mode2 = [animal[0] for animal in query.all()][0].split(', ')
                session.close()

                res = make_response()
                res.set_cookie('list_button_img_mode2', json.dumps(list_button_img_mode2))
                res.set_cookie('audio', str(lst_tasks[task.correct_question][0]))

    def restart_level(self):
        res = make_response()
        res.set_cookie("correct_question", '0')
        res.set_cookie("lst_imgs", json.dumps([]))

    def update_level(self):
        res = make_response()
        res.set_cookie("user_points_mode1", '100')
        res.set_cookie("user_points_mode2", '100')
        res.set_cookie("curent_hint", '0')

        self.restart_level()
        self.texts_by_level()

    def get_all_from_task(self):
        task.get_random_id()
        task.get_tasks_by_random_id()
        task.get_name_animal()


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
    if request.method == 'POST':
        selected_mode = request.form.get('btn')

        if selected_mode == "1":
            return redirect("/update_level_one")
        elif selected_mode == "2":
            return redirect("/update_level_two")

    return render_template('select_level.html')


@app.route('/mode_one', methods=['GET', 'POST'])
def mode_one():
    if request.method == 'POST':
        selected_answer = request.form.get('btn')

        lst_tasks = eval(request.cookies.get('lst_tasks'))
        correct_question = int(request.cookies.get('correct_question'))
        lst_tasks = eval(request.cookies.get('lst_tasks'))
        lst_imgs = eval(request.cookies.get('lst_imgs'))
        count_wrong_answer = int(request.cookies.get('count_wrong_answer'))
        user_points_mode1 = int(request.cookies.get('user_points_mode1'))

        if selected_answer == lst_tasks[correct_question][1]:
            correct_question += 1
            lst_imgs.append(lst_tasks[correct_question - 1][2])
            count_wrong_answer = 0
            task.texts_by_level()
        else:
            count_wrong_answer += 1
            user_points_mode1 -= 5
            if count_wrong_answer == 2:
                user_points_mode1 -= 5
                count_wrong_answer = 0
                task.restart_level()
                task.texts_by_level()
            if user_points_mode1 < 0:
                user_points_mode1 = 0

        response = make_response()
        response.set_cookie('correct_question', str(correct_question))
        response.set_cookie('lst_imgs', str(lst_imgs))
        response.set_cookie('count_wrong_answer', str(count_wrong_answer))
        response.set_cookie('user_points_mode1', str(user_points_mode1))

    if request.method == 'GET':
        user_input = request.args.get('animal')

        name_animal = request.cookies.get('name_animal')
        user_points_mode1 = int(request.cookies.get('user_points_mode1'))

        if user_input is not None:
            if user_input.lower().strip() == name_animal:
                db_sess = db_session.create_session()
                user = db_sess.query(User).filter(User.id == current_user.id).first()
                user.user_points_mode1 += user_points_mode1
                db_sess.commit()

                return redirect("/select_level")
            else:
                user_points_mode1 -= 5
                response = make_response()
                response.set_cookie('user_points_mode1', str(user_points_mode1))
        else:
            response = make_response()
            response.set_cookie('flag_hint', 'True')
            curent_hint = int(request.cookies.get('curent_hint'))
            name_animal = request.cookies.get('name_animal')
            if curent_hint == 1:
                hint_text = f"Букв в слове: {len(str(name_animal))}"
                user_points_mode1 -= 10
                btn_hint_text = "Подсказка"
            elif curent_hint == 2:
                hint_text = f"Первая буква: {name_animal[0]}"
                user_points_mode1 -= 10
                btn_hint_text = "Сдаюсь"
            elif curent_hint >= 3:
                hint_text = f"Правильный ответ: {name_animal}"
                user_points_mode1 = 0
                flag_hint = False
            else:
                hint_text = ""
                btn_hint_text = "Подсказка"
            curent_hint += 1

            response.set_cookie('hint_text', str(hint_text))
            response.set_cookie('user_points_mode1', str(user_points_mode1))
            response.set_cookie('btn_hint_text', str(btn_hint_text))
            response.set_cookie('flag_hint', str(flag_hint))

            question = request.cookies.get('question')
            list_button_text_mode1 = eval(request.cookies.get('list_button_text_mode1'))
            lst_imgs = eval(request.cookies.get('lst_imgs'))
            correct_question = int(request.cookies.get('correct_question'))
            lst_tasks = eval(request.cookies.get('lst_tasks'))

            return render_template('mode_one.html', question=question,
                                   btn_texts=list_button_text_mode1, file_imgs=lst_imgs,
                                   user_points=user_points_mode1, correct_question=correct_question,
                                   len_lst_tasks=len(lst_tasks), name_animal=name_animal,
                                   curent_hint=curent_hint, hint_text=hint_text,
                                   btn_hint_text=btn_hint_text, flag=flag_hint)
    flag_hint = True
    response = make_response()
    response.set_cookie('flag_hint', str(flag_hint))

    question = request.cookies.get('question')
    list_button_text_mode1 = eval(request.cookies.get('list_button_text_mode1'))
    lst_imgs = eval(request.cookies.get('lst_imgs'))
    user_points_mode1 = int(request.cookies.get('user_points_mode1'))
    correct_question = int(request.cookies.get('correct_question'))
    lst_tasks = eval(request.cookies.get('lst_tasks'))
    name_animal = request.cookies.get('name_animal')
    curent_hint = int(request.cookies.get('curent_hint'))
    hint_text = request.cookies.get('hint_text')
    btn_hint_text = request.cookies.get('btn_hint_text')

    return render_template('mode_one.html', question=question,
                           btn_texts=list_button_text_mode1, file_imgs=lst_imgs,
                           user_points=user_points_mode1, correct_question=correct_question,
                           len_lst_tasks=len(lst_tasks), name_animal=name_animal,
                           curent_hint=curent_hint, hint_text=hint_text,
                           btn_hint_text=btn_hint_text, flag=flag_hint)


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
                response = make_response()
                response.set_cookie('user_points_mode2', str(user_points_mode2))

        else:
            response = make_response()
            response.set_cookie('flag_hint', 'True')
            curent_hint = int(request.cookies.get('curent_hint'))
            name_animal = request.cookies.get('name_animal')
            if curent_hint == 1:
                hint_text = f"Букв в слове: {len(str(name_animal))}"
                user_points_mode2 -= 10
                btn_hint_text = "Подсказка"
            elif curent_hint == 2:
                hint_text = f"Первая буква: {name_animal[0]}"
                user_points_mode2 -= 10
                btn_hint_text = "Сдаюсь"
            elif curent_hint >= 3:
                hint_text = f"Правильный ответ: {name_animal}"
                user_points_mode2 = 0
                flag_hint = False
            else:
                hint_text = ""
                btn_hint_text = "Подсказка"
            curent_hint += 1

            response.set_cookie('hint_text', str(hint_text))
            response.set_cookie('user_points_mode2', str(user_points_mode2))
            response.set_cookie('btn_hint_text', str(btn_hint_text))
            response.set_cookie('flag_hint', str(flag_hint))

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
                                   curent_hint=curent_hint, hint_text=hint_text,
                                   btn_hint_text=btn_hint_text, flag=flag_hint)
    flag_hint = True
    response = make_response()
    response.set_cookie('flag_hint', str(flag_hint))

    list_button_img_mode2 = eval(request.cookies.get('list_button_img_mode2'))
    lst_imgs = eval(request.cookies.get('lst_imgs'))
    user_points_mode2 = int(request.cookies.get('user_points_mode2'))
    audio = request.cookies.get('audio')
    correct_question = int(request.cookies.get('correct_question'))
    lst_tasks = eval(request.cookies.get('lst_tasks'))
    name_animal = request.cookies.get('name_animal')
    curent_hint = int(request.cookies.get('curent_hint'))
    hint_text = request.cookies.get('hint_text')
    btn_hint_text = request.cookies.get('btn_hint_text')

    return render_template('mode_two.html', question="Послушай диктора и выбери названную им фигуру",
                           btn_imges=list_button_img_mode2, file_imgs=lst_imgs,
                           user_points=user_points_mode2, correct_audio=audio,
                           correct_question=correct_question,
                           len_lst_tasks=len(lst_tasks), name_animal=name_animal,
                           curent_hint=curent_hint, hint_text=hint_text,
                           btn_hint_text=btn_hint_text, flag=flag_hint)


@app.route('/leader_board')
def leader_board():
    db_sess = db_session.create_session()
    users = db_sess.query(User).all()

    user_points = [(user.user_points_mode1 + user.user_points_mode2, user) for user in users]

    sorted_users = sorted(user_points, key=lambda x: x[0], reverse=True)

    enumerated_users = [(index + 1, user) for index, (_, user) in enumerate(sorted_users)]
    print(enumerated_users)
    return render_template('leader_board.html', users=enumerated_users)


@app.route('/update_level_one')
def update_level_one():
    lst_tasks = []
    mode_value = 1
    response = make_response()
    response.set_cookie('lst_tasks', str(lst_tasks))
    response.set_cookie('mode_value', str(mode_value))

    task.get_all_from_task()

    task.update_level()
    return redirect("/mode_one")


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
    task = Task()

    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

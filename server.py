import os
import random

from pprint import pprint

from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

from flask import Flask, render_template, redirect, request, jsonify
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
        self.correct_question = 0
        self.count_wrong_answer = 0
        self.user_points_mode1 = 100
        self.user_points_mode2 = 100
        self.curent_hint = 0
        self.btn_hint_text = "Подсказка"
        self.hint_text = ""
        self.lst_tasks = []
        self.lst_imgs = []

    def get_random_id(self, mode_value):
        self.mode_value = mode_value

        Session = sessionmaker(bind=engine)
        session = Session()

        query = session.query(Animal.id).filter(Animal.mode == mode_value)
        self.ides = [animal[0] for animal in query.all()]

        session.close()

        self.random_id = random.choice(self.ides)

        return self.random_id

    def get_tasks_by_random_id(self, random_id, mode_value):
        if mode_value == 1:
            Session = sessionmaker(bind=engine)
            session = Session()

            query_tasks = session.query(ModeOne.tasks).filter(ModeOne.id_animal == random_id)
            query_pnges = session.query(ModeOne.answers).filter(ModeOne.id_animal == random_id)
            query_pngs = session.query(ModeOne.png).filter(ModeOne.id_animal == random_id)

            for task, answer, png in zip(query_tasks, query_pnges, query_pngs):
                lst_task = [task[0], answer[0], png[0]]
                self.lst_tasks.append(lst_task)
            session.close()

        elif mode_value == 2:
            Session = sessionmaker(bind=engine)
            session = Session()

            query_mp3es = session.query(ModeTwo.mp3).filter(ModeTwo.id_animal == random_id)
            query_pnges = session.query(ModeTwo.png).filter(ModeTwo.id_animal == random_id)
            query_answers = session.query(ModeTwo.answer).filter(ModeTwo.id_animal == random_id)
            for mp3, png, answer in zip(query_mp3es, query_pnges, query_answers):
                lst_task = [mp3[0], png[0], answer[0]]
                self.lst_tasks.append(lst_task)
            session.close()
        random.shuffle(self.lst_tasks)
        self.texts_by_level(self.mode_value)

    def get_name_animal(self, random_id):
        Session = sessionmaker(bind=engine)
        session = Session()

        self.name_animal = session.query(Animal.oset_name).filter(Animal.id == random_id).first()
        session.close()
        self.name_animal = self.name_animal[0]

    def texts_by_level(self, mode_value):
        if self.correct_question != len(self.lst_tasks):
            if mode_value == 1:
                list_random_wrong_words = []
                while len(list_random_wrong_words) < 3:
                    random_index = random.choice(range(len(self.lst_tasks)))
                    if random_index != self.correct_question and random_index not in list_random_wrong_words:
                        list_random_wrong_words.append(random_index)

                self.list_button_text_mode1 = [self.lst_tasks[self.correct_question][1],
                                               self.lst_tasks[list_random_wrong_words[0]][1],
                                               self.lst_tasks[list_random_wrong_words[1]][1],
                                               self.lst_tasks[list_random_wrong_words[2]][1]]
                random.shuffle(self.list_button_text_mode1)
                self.question = self.lst_tasks[task.correct_question][0]
            elif mode_value == 2:
                Session = sessionmaker(bind=engine)
                session = Session()

                query = session.query(Animal.shape_used).filter(Animal.id == self.random_id)
                self.list_button_img_mode2 = [animal[0] for animal in query.all()][0].split(', ')
                session.close()

                self.audio = self.lst_tasks[task.correct_question][0]

    def restart_level(self):
        self.correct_question = 0
        self.lst_imgs.clear()


def update_level():
    task.user_points_mode1, task.user_points_mode2 = 100, 100
    task.curent_hint = 0
    task.restart_level()
    task.texts_by_level(task.mode_value)


def get_all_from_task(mode_value):
    random_id = task.get_random_id(mode_value)
    print(random_id)
    task.get_tasks_by_random_id(random_id, mode_value)
    pprint(task.lst_tasks)
    task.get_name_animal(random_id)


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

        if selected_answer == task.lst_tasks[task.correct_question][1]:
            task.correct_question += 1
            task.lst_imgs.append(task.lst_tasks[task.correct_question - 1][2])
            task.count_wrong_answer = 0
            task.texts_by_level(task.mode_value)
        else:
            task.count_wrong_answer += 1
            task.user_points_mode1 -= 5
            if task.count_wrong_answer == 2:
                task.user_points_mode1 -= 5
                task.count_wrong_answer = 0
                task.restart_level()
                task.texts_by_level(task.mode_value)
            if task.user_points_mode1 < 0:
                task.user_points_mode1 = 0

    if request.method == 'GET':
        user_input = request.args.get('animal')

        if user_input is not None:
            if user_input.lower().strip() == task.name_animal:
                db_sess = db_session.create_session()
                user = db_sess.query(User).filter(User.id == current_user.id).first()
                user.user_points_mode1 += task.user_points_mode1
                db_sess.commit()

                return redirect("/select_level")

        else:
            flag = True
            if task.curent_hint == 1:
                task.hint_text = f"Букв в слове: {len(str(task.name_animal))}"
                task.user_points_mode1 -= 10
                task.btn_hint_text = "Подсказка"
            elif task.curent_hint == 2:
                task.hint_text = f"Первая буква: {str(task.name_animal)[0]}"
                task.user_points_mode1 -= 10
                task.btn_hint_text = "Сдаюсь"
            elif task.curent_hint >= 3:
                task.hint_text = f"Правильный ответ: {task.name_animal}"
                task.user_points_mode1 = 0
                flag = False
            else:
                task.hint_text = ""
                task.btn_hint_text = "Подсказка"
            task.curent_hint += 1
            return render_template('mode_one.html', question=task.question,
                                   btn_texts=task.list_button_text_mode1, file_imgs=task.lst_imgs,
                                   user_points=task.user_points_mode1, correct_question=task.correct_question,
                                   len_lst_tasks=len(task.lst_tasks), name_animal=task.name_animal,
                                   curent_hint=task.curent_hint, hint_text=task.hint_text,
                                   btn_hint_text=task.btn_hint_text,
                                   flag=flag)
    flag = True
    return render_template('mode_one.html', question=task.question,
                           btn_texts=task.list_button_text_mode1, file_imgs=task.lst_imgs,
                           user_points=task.user_points_mode1, correct_question=task.correct_question,
                           len_lst_tasks=len(task.lst_tasks), name_animal=task.name_animal,
                           curent_hint=task.curent_hint, hint_text=task.hint_text, btn_hint_text=task.btn_hint_text,
                           flag=flag)


@app.route('/mode_two', methods=['GET', 'POST'])
def mode_two():
    if request.method == 'POST':
        selected_answer = request.form.get('btn')
        if selected_answer == task.lst_tasks[task.correct_question][2]:
            task.correct_question += 1
            task.lst_imgs.append(task.lst_tasks[task.correct_question - 1][1])
            task.count_wrong_answer = 0
            task.texts_by_level(task.mode_value)

        else:
            task.count_wrong_answer += 1
            task.user_points_mode2 -= 5
            if task.count_wrong_answer == 3:
                task.user_points_mode2 -= 5
                task.count_wrong_answer = 0
                task.restart_level()
                task.texts_by_level(task.mode_value)
            if task.user_points_mode2 < 0:
                task.user_points_mode2 = 0

    if request.method == 'GET':
        user_input = request.args.get('animal')

        if user_input is not None:
            if user_input.lower().strip() == task.name_animal:
                db_sess = db_session.create_session()
                user = db_sess.query(User).filter(User.id == current_user.id).first()
                user.user_points_mode2 += task.user_points_mode2
                db_sess.commit()

                return redirect("/select_level")
        else:
            flag = True
            if task.curent_hint == 1:
                task.hint_text = f"Букв в слове: {len(str(task.name_animal))}"
                task.user_points_mode2 -= 10
                task.btn_hint_text = "Подсказка"
            elif task.curent_hint == 2:
                task.hint_text = f"Первая буква: {str(task.name_animal)[0]}"
                task.user_points_mode2 -= 10
                task.btn_hint_text = "Сдаюсь"
            elif task.curent_hint >= 3:
                task.hint_text = f"Правильный ответ: {task.name_animal}"
                task.user_points_mode2 = 0
                flag = False
            else:
                task.hint_text = ""
                task.btn_hint_text = "Подсказка"
            task.curent_hint += 1
            return render_template('mode_two.html', question="Послушай диктора и выбери названную им фигуру",
                                   btn_imges=task.list_button_img_mode2, file_imgs=task.lst_imgs,
                                   user_points=task.user_points_mode2, correct_audio=task.audio,
                                   correct_question=task.correct_question,
                                   len_lst_tasks=len(task.lst_tasks), name_animal=task.name_animal,
                                   curent_hint=task.curent_hint, hint_text=task.hint_text,
                                   btn_hint_text=task.btn_hint_text, flag=flag)
    flag = True
    return render_template('mode_two.html', question="Послушай диктора и выбери названную им фигуру",
                           btn_imges=task.list_button_img_mode2, file_imgs=task.lst_imgs,
                           user_points=task.user_points_mode2, correct_audio=task.audio,
                           correct_question=task.correct_question,
                           len_lst_tasks=len(task.lst_tasks), name_animal=task.name_animal,
                           curent_hint=task.curent_hint, hint_text=task.hint_text,
                           btn_hint_text=task.btn_hint_text, flag=flag)


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
    task.lst_tasks.clear()
    mode_value = 1
    get_all_from_task(mode_value)

    update_level()
    return redirect("/mode_one")


@app.route('/update_level_two')
def update_level_two():
    task.lst_tasks.clear()
    mode_value = 2
    get_all_from_task(mode_value)

    update_level()
    return redirect("/mode_two")


if __name__ == '__main__':
    db_session.global_init("db/DataBase.db")
    task = Task()

    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

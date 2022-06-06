
import datetime
import os

from db_config import host, db_name
import pymysql

from flask import Flask, render_template, request, redirect, session, url_for, abort, flash 


class SelectPreparator:
    def select_songs(self):
        query = "SELECT  `song_name`, `author_pseudo` FROM `composition` JOIN `author` ON composition.author_id = author.author_id JOIN `song` ON composition.song_id = song.song_id"
        return query
    
    def select_respondent_id_by_email(self,form):
         query = f"SELECT `respondent_id` FROM `respondent` WHERE respondent_email = '{form['email']}'"
         return query

    def select_respondent_pass_sex_age_by_email(self,form):
        query = f"SELECT `password`,`respondent_sex` as sex, `respondent_age` as age FROM `respondent` WHERE respondent_email = '{form['email']}'"
        return query

    def select_respondent_from_survey(self,resp_id):
        query = f"SELECT * FROM survey_result WHERE survey_id = 1 and respondent_id = {resp_id}"
        return query

    def select_composition_id(self,form, song_key):
        song_name =  ''.join(["\\'" if s == "'" else s for s in form[song_key].split('-')[1].strip()])
        author_pseudo = ''.join(["\\'" if s == "'" else s for s in form[song_key].split('-')[0].strip()])
        query = f"SELECT `id` FROM `composition` JOIN `song` ON composition.song_id = song.song_id JOIN `author` ON composition.author_id = author.author_id WHERE  song_name = '{song_name}' AND author_pseudo = '{author_pseudo}' "
        return query

    def select_male_playlist(self):
        query = "SELECT * FROM get_male_playlist_id"
        return query
    
    def select_male_songs(self):
        query = "SELECT * FROM `songs_for_males_playlist`"
        return query
    
    def select_female_playlist(self):
        query = "SELECT * FROM get_female_playlist_id"
        return query
    
    def select_female_songs(self):
        query = "SELECT * FROM `songs_for_females_playlist`"
        return query
    
    def select_youngster_playlist(self):
        query = "SELECT * FROM get_youngsters_playlist_id"
        return query
    
    def select_youngster_songs(self):
        query = "SELECT * FROM `songs_for_youngsters_playlist`"
        return query
    
    def select_all_playlists(self):
        query = "SELECT * FROM `get_each_playlist`"
        return query
    
    def select_password_by_email(self,form):
        query = f"SELECT `password` FROM `respondent` WHERE respondent_email = '{form['email']}'"
        return query

class InsertPreparator:
    def insert_respondent(self,form):
        query = f"INSERT INTO `respondent` (`respondent_sex`,`respondent_age`,`respondent_email`) VALUES ('{form['sex']}',{form['age']},'{form['email']}')"
        return query
    
    def insert_respondent_with_password(self,form):
        query = f"INSERT INTO `respondent` (`respondent_sex`,`respondent_age`,`respondent_email`, `password`) VALUES ('{form['sex']}',{form['age']},'{form['email']}', '{form['password']}')"
        return query

    def insert_survey_result(self,form):
        select_preparator = SelectPreparator()
        if (session.get('user_data') or database.insert(self.insert_respondent(form))):
            select_resp_result = database.select(select_preparator.select_respondent_id_by_email(form))
            respondent_id = select_resp_result[0]['respondent_id']

            survey_validator = SurveyValidator()
            if not survey_validator.validate_survey_result_insert(respondent_id):
                flash('user has already run the survey', 'error')
                return None
            
            insert_query = "INSERT INTO `survey_result` (`survey_id`, `composition_id`, `respondent_id`) VALUES "
            for i in range(5):
                song_key_json = f'song{i+1}'
                result = database.select(select_preparator.select_composition_id(form, song_key_json))
                composition_id = result[0]['id']
                insert_query += f"(1, {composition_id}, {respondent_id})," # инсерт в опрос с идом 1

            flash('the survey has been successfully run', 'success')
            return insert_query[:-1]
        
        flash('user has already run the survey', 'error')
        return None

    def insert_playlist(self, songs, playlist_id):
        query = "INSERT INTO `playlist_inner` (`playlist_id`, `composition_id`) VALUES "
        for song in songs:
            query += f"({playlist_id}, {song['composition_id']}),"
        return query[:-1]

class UpdatePreparator:
    def update_password(self,form):
        query = f"UPDATE `respondent` SET password = '{form['password']}', respondent_age = {form['age']}, respondent_sex = '{form['sex']}' WHERE respondent_email = '{form['email']}'"
        return query

class DeletePreparator:
    def delete_playlist(self,playlist_id):
        query = f"DELETE FROM `playlist_inner` WHERE playlist_id = {playlist_id}"
        return query

class PlaylistsUpdater:

    def update_playlist(self,select_playlist, select_songs_for_playlist):
        delete_preparator = DeletePreparator()
        insert_preparator = InsertPreparator()

        try:
            playlist_id = database.select(select_playlist())[0]['playlist_id']
            database.delete(delete_preparator.delete_playlist(playlist_id))

            songs = database.select(select_songs_for_playlist())
            database.insert(insert_preparator.insert_playlist(songs,playlist_id))
        
        except Exception as e:
            print('update Playlist Error: ', e)

    def update_playlists(self,form):
        select_preparator = SelectPreparator()

        if form['sex'] == 'M':
            self.update_playlist(select_preparator.select_male_playlist,select_preparator.select_male_songs)
        elif form['sex'] == 'F':
            self.update_playlist(select_preparator.select_female_playlist,select_preparator.select_female_songs)
        if int(form['age']) <= 21:
            self.update_playlist(select_preparator.select_youngster_playlist,select_preparator.select_youngster_songs)

class Db:
    def __init__(self, user, password):
        try:

            self.connection = pymysql.connect (
                host = host,
                user = user,
                password= password,
                database=db_name,
                cursorclass=pymysql.cursors.DictCursor
            )
        
            print("Successfully connected...")


        except Exception as e:
            print("Connection failed...",e)
            
    

    def select(self,query):
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query)
                result = cursor.fetchall()
                return result
        except:
            print("selection Error: ",query)

    def insert(self,query):
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query)
                self.connection.commit()
                return True
        except:
            print("insertion Error: ",query)
            return False

    def update(self,query):
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query)
                self.connection.commit()
        except:
            print('update Error: ', query)

    def delete(self,query):
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query)
                self.connection.commit()
        except:
            print('delete Error: ', query)

            
class Writer:
    def write_to_file(self,data, filename):
    
        with open(filename, 'wb') as file:
            file.write(data)
        print("Данные сохранены в: ", filename, "\n")


class Formatter:

    def format_raw_playlists_cat_img(self,raw_playlists):
            writer = Writer()
            for raw_playlist in raw_playlists:
                    photo_path = os.path.join("static\imgs\\", raw_playlist['category_name'] + ".jpg")
                    writer.write_to_file(raw_playlist['category_image'], photo_path)
                    raw_playlist['category_image'] = photo_path

            return raw_playlists


    def format_raw_playlists_as_dict(self):
            select_preparator = SelectPreparator()
            raw_playlists = database.select(select_preparator.select_all_playlists())

            raw_playlists = self.format_raw_playlists_cat_img(raw_playlists)
            ready_playlists = {}
            for raw_playlist in raw_playlists:
                if ready_playlists.get((raw_playlist['category_name'], raw_playlist['category_image'])) is None:
                    ready_playlists[(raw_playlist['category_name'], raw_playlist['category_image'])] = [raw_playlist['author_pseudo'] + ' - ' + raw_playlist['song_name']]
                else:
                    ready_playlists[(raw_playlist['category_name'], raw_playlist['category_image'])].append(raw_playlist['author_pseudo'] + ' - ' + raw_playlist['song_name'])
            return ready_playlists


class SurveyValidator:
    def validate_survey_result_insert(self,resp_id):
        if session.get('user_data'):
            select_preparator = SelectPreparator()
            result = database.select(select_preparator.select_respondent_from_survey(resp_id))
            if (result):
                return False
        return True


class UserValidator:

    def validate_login(self,form,session):
        select_preparator = SelectPreparator()
        user_data = database.select(select_preparator.select_respondent_pass_sex_age_by_email(form))

        if user_data:
            if (form['password'] == user_data[0]['password']):
                del user_data[0]['password']
                user_data[0]['email'] = form['email']
                session['user_data'] = user_data[0]

                flash('successfully logged in', 'success')
                return True
            else:
                flash('incorrect password', 'error')

                return False

        flash('no respondent found', 'error')

        return False
    
    def validate_register(self,form):
        select_preparator = SelectPreparator()
        insert_preparator = InsertPreparator()
        update_preparator = UpdatePreparator()

        user = database.select(select_preparator.select_password_by_email(form))

        if not user:
            if form['password'] == form['confirm']:
                database.insert(insert_preparator.insert_respondent_with_password(form))
                flash('successfully registered', 'success')
                return True
            else:
                flash('passwords don\'t match','error')    
                return False
        elif user[0]['password'] == None:
            if form['password'] == form['confirm']:
                database.update(update_preparator.update_password(form))
                flash('successfully registered', 'success')
            else:
                flash('passwords don\'t match', 'error')
                return False
            return True
        else:
            flash('the user already exists', 'error')
            return False
            

class RoutesFormProcessor:
    select_preparator = SelectPreparator()
    insert_preparator = InsertPreparator()
    playlist_updater = PlaylistsUpdater()

    def process_guest_form(self,form):
        survey_results = self.insert_preparator.insert_survey_result(form)
        database.insert(survey_results)
        self.playlist_updater.update_playlists(request.form) 

    def process_registered_user_form(self,form,session):
        new_form = {'age':session['user_data']['age'],'sex':session['user_data']['sex'],'email':session['user_data']['email']}
        new_form.update(form.to_dict())
        survey_results = self.insert_preparator.insert_survey_result(new_form)
        if survey_results:
            database.insert(survey_results)
            self.playlist_updater.update_playlists(new_form)
    
    def process_admin_form(self,form,session):
        new_form = {'age':session['user_data']['age'],'sex':session['user_data']['sex'],'email':session['user_data']['email']}
        new_form.update(form.to_dict())
        survey_results = self.insert_preparator.insert_survey_result(new_form)
        if survey_results:
            database.insert(survey_results)
            self.playlist_updater.update_playlists(new_form)
    

app = Flask(__name__)
app.config['SECRET_KEY'] = 'bc83989cdfdd894859fkdlfd83i489ffjdj99'
app.permanent_session_lifetime = datetime.timedelta(days=1)


@app.route("/", methods=['GET','POST']) 
def hub():
    session.permanent = True
    global database

    if session.get('user_data'):
        if (session['user_data']['email'] == 'admin@admin.ru'):

            database = Db('admin','admin')
            return redirect('/admin')
        
        database = Db('registered_user','user')
        
        return redirect('/registered')

    #unregistered
    database = Db('guest','guest')

    select_preparator = SelectPreparator()
    songs = database.select(select_preparator.select_songs())

    routes_processor = RoutesFormProcessor()
    if request.method == "POST" and request.form != []:
        routes_processor.process_guest_form(request.form)

    return render_template("unregistered_main.html", songs=songs)

@app.route("/registered", methods=['GET','POST'])
def registered():
    if not session.get('user_data'):
        abort(404)
    
    select_preparator = SelectPreparator()
    songs = database.select(select_preparator.select_songs())
    
    routes_processor = RoutesFormProcessor()
    if request.method == "POST" and request.form != []:
        routes_processor.process_registered_user_form(request.form,session)
        
    return render_template("registered_main.html", songs=songs, email=session['user_data']['email'])

@app.route("/admin", methods=['GET','POST']) 
def admin():
    if not session.get('user_data') or session['user_data']['email'] != 'admin@admin.ru':
        abort(404)

    select_preparator = SelectPreparator()
    songs = database.select(select_preparator.select_songs())

    routes_processor = RoutesFormProcessor()
    if request.method == "POST" and request.form != []:
        routes_processor.process_admin_form(request.form,session)

    return render_template("admin_main.html", songs=songs, email=session['user_data']['email'])

@app.route("/registered_playlists")
def registered_playlists():
    if not session.get('user_data'):
        abort(404)

    formatter = Formatter()
    playlists = formatter.format_raw_playlists_as_dict()
    return render_template("registered_playlists.html", playlists=playlists.items(), email=session['user_data']['email'])

@app.route("/admin_playlists")
def admin_playlists():
    if not session.get('user_data') or session['user_data']['email'] != 'admin@admin.ru':
        abort(404)

    formatter = Formatter()
    playlists = formatter.format_raw_playlists_as_dict()
    return render_template("admin_playlists.html", playlists=playlists.items(),email=session['user_data']['email'])


@app.route("/login", methods=['GET','POST'])
def login():
    user_validator = UserValidator()
    if request.method == "POST" and user_validator.validate_login(request.form, session):
        return redirect('/')
    
    return render_template("login.html")


@app.route("/logout")
def logout():
    session['user_data'] = None
    return redirect('/')


@app.route("/register", methods=['GET','POST'])
def register():
    user_validator = UserValidator()
    if request.method == 'POST' and user_validator.validate_register(request.form):
        session['user_data'] = {'email':request.form['email'], 'sex':request.form['sex'], 'age': request.form['age']}
        return redirect('/')

    return render_template("register.html")


if __name__ == "__main__":
    app.run(debug=True)

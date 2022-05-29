

import datetime
import os

import pymysql
from db_config import host, user, password, db_name

from flask import Flask, render_template, request, redirect, session, url_for, abort, flash 

connection = None
def db_connect(user,password):
    try:
        global connection

        connection = pymysql.connect(
            host = host,
            user = user,
            password= password,
            database=db_name,
            cursorclass=pymysql.cursors.DictCursor
        )
        
        print("Successfully connected...")


    except Exception as ex:
        print("Connection failed...")
        print(ex)

def select_songs():
    result = ()
    with connection.cursor() as cursor:
        query = "SELECT  `song_name`, `author_pseudo` FROM `composition` JOIN `author` ON composition.author_id = author.author_id JOIN `song` ON composition.song_id = song.song_id"
        cursor.execute(query)
        result = cursor.fetchall()
    return result


def insert_respondent(form):
    
    try:

        with connection.cursor() as cursor:
            if not form.get('password'):
                query = f"INSERT INTO `respondent` (`respondent_sex`,`respondent_age`,`respondent_email`) VALUES ('{form['sex']}',{form['age']},'{form['email']}')"
                
            else:
                cursor.execute(f"SELECT `password` FROM `respondent` WHERE respondent_email = '{form['email']}'")
                user = cursor.fetchall()
                
                if not user:
                    if form['password'] == form['confirm']:
                        query = f"INSERT INTO `respondent` (`respondent_sex`,`respondent_age`,`respondent_email`, `password`) VALUES ('{form['sex']}',{form['age']},'{form['email']}', '{form['password']}')"
                        flash('successfully registered', 'success')
                    else:
                        flash('passwords don\'t match','error')    
                elif user[0]['password'] == None:
                    query = f"UPDATE `respondent` SET password = '{form['password']}', respondent_age = {form['age']}, respondent_sex = '{form['sex']}' WHERE respondent_email = '{form['email']}'"
                    flash('successfully registered', 'success')
                else:
                    flash('the user already exists', 'error')
            
            cursor.execute(query)
            connection.commit()
        
        return True
    except:
        print("respondent Error")

        return False
    

def insert_survey_result(form):
    
    if (session.get('user_data') or insert_respondent(form)):
        try:

            with connection.cursor() as cursor:
                query = f"SELECT `respondent_id` FROM `respondent` WHERE respondent_email = '{form['email']}'"
                cursor.execute(query)

                respondent_id = cursor.fetchall()[0]['respondent_id']

                if session.get('user_data'):
                    cursor.execute(f"SELECT * FROM survey_result WHERE survey_id = 1 and respondent_id = {respondent_id}")
                    if (cursor.fetchall()):
                        flash('user has already run the survey', 'error')

                        print('registered user is already in survey_result')
                        return False

                insert_query = "INSERT INTO `survey_result` (`survey_id`, `composition_id`, `respondent_id`) VALUES "
                for i in range(5):
                    song_key_json = f'song{i+1}'
                    
                    cursor.execute(f"SELECT `id` FROM `composition` JOIN `song` ON composition.song_id = song.song_id JOIN `author` ON composition.author_id = author.author_id WHERE  song_name = '{form[song_key_json].split('-')[1].strip()}' AND author_pseudo = '{form[song_key_json].split('-')[0].strip()}' ")
                    composition_id = cursor.fetchall()[0]['id']

                    insert_query += f"(1, {composition_id}, {respondent_id})," # инсерт в опрос с идом 1

                cursor.execute(insert_query[:-1])
                connection.commit()

                flash('the survey has been successfully run', 'success')
                return True
        except:
            print("survey_result Error")
            return False

    flash('user has already run the survey', 'error')
    return False

def update_playlist(form):
    
    with connection.cursor() as cursor:
        if (form['sex'] == 'M'):

            cursor.execute("SELECT * FROM get_male_playlist_id")
            playlist_id = cursor.fetchall()[0]['playlist_id']
            
            try:

                cursor.execute(f"DELETE FROM `playlist_inner` WHERE playlist_id = {playlist_id}")

                cursor.execute("SELECT * FROM `songs_for_males_playlist`")
                songs = cursor.fetchall()

                insert_playlist_query = "INSERT INTO `playlist_inner` (`playlist_id`, `composition_id`) VALUES "
                for song in songs:
                    insert_playlist_query += f"({playlist_id}, {song['composition_id']}),"
                
                cursor.execute(insert_playlist_query[:-1])
                connection.commit()
            except:
                print("update_playlist Error")
                connection.rollback()

            print(songs)

        elif (form['sex'] == 'F'):

            cursor.execute("SELECT * FROM get_female_playlist_id")
            playlist_id = cursor.fetchall()[0]['playlist_id']
            
            try:

                cursor.execute(f"DELETE FROM `playlist_inner` WHERE playlist_id = {playlist_id}")

                cursor.execute("SELECT * FROM `songs_for_females_playlist`")
                songs = cursor.fetchall()

                insert_query = "INSERT INTO `playlist_inner` (`playlist_id`, `composition_id`) VALUES "
                for song in songs:
                    insert_query += f"({playlist_id}, {song['composition_id']}),"
                
                cursor.execute(insert_query[:-1])
                connection.commit()
            except:
                print("update_playlist Error")
                connection.rollback()
            print(songs)
        
        if (int(form['age']) <= 21):

            cursor.execute("SELECT * FROM get_youngsters_playlist_id")
            playlist_id = cursor.fetchall()[0]['playlist_id']

            try:

                cursor.execute(f"DELETE FROM `playlist_inner` WHERE playlist_id = {playlist_id}")

                cursor.execute("SELECT * FROM `songs_for_youngsters_playlist`")
                songs = cursor.fetchall()

                insert_query = "INSERT INTO `playlist_inner` (`playlist_id`, `composition_id`) VALUES "
                for song in songs:
                    insert_query += f"({playlist_id}, {song['composition_id']}),"
                
                cursor.execute(insert_query[:-1])
                connection.commit()
            except:
                print("update_playlist Error")
                connection.rollback()
            print(songs)


def format_raw_playlists(raw_playlists):
    ready_playlists = {}
    for raw_playlist in raw_playlists:
        if ready_playlists.get((raw_playlist['category_name'], raw_playlist['category_image'])) is None:
            ready_playlists[(raw_playlist['category_name'], raw_playlist['category_image'])] = [raw_playlist['author_pseudo'] + ' - ' + raw_playlist['song_name']]
        else:
            ready_playlists[(raw_playlist['category_name'], raw_playlist['category_image'])].append(raw_playlist['author_pseudo'] + ' - ' + raw_playlist['song_name'])
    print(ready_playlists)
    return ready_playlists       


def write_to_file(data, filename):
    
    with open(filename, 'wb') as file:
        file.write(data)
    print("Данный из blob сохранены в: ", filename, "\n")

def get_ready_playlists():
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM `get_each_playlist`")
        raw_playlists = cursor.fetchall()
        
        for raw in raw_playlists:
             photo_path = os.path.join("static\imgs\\", raw['category_name'] + ".jpg")
             write_to_file(raw['category_image'], photo_path)
             raw['category_image'] = photo_path
        
        
        return format_raw_playlists(raw_playlists)

def validate_user(form, session):
    with connection.cursor() as cursor:     
        cursor.execute(f"SELECT `password`,`respondent_sex` as sex, `respondent_age` as age FROM `respondent` WHERE respondent_email = '{form['email']}'")
        user_data = cursor.fetchall()
        if user_data:
            if (form['password'] == user_data[0]['password']):
                del user_data[0]['password']
                user_data[0]['email'] = form['email']
                session['user_data'] = user_data[0]

                flash('successfully logged in', 'success')
                return True
            else:
                flash('incorrect password', 'error')

                print('incorrect password')
                return False

        flash('no respondent found', 'error')

        print('no respondent')
        return False

def stat_query():
    query_tables = {}
    with connection.cursor() as cursor:
        
        cursor.execute("SELECT * FROM stats_total_listeners_for_each_song")
        query_tables["Кол-во слушателей на каждую песню: "] = cursor.fetchall()

        cursor.execute("SELECT * FROM stats_song_with_max_listeners")
        query_tables["Песни c макс. слушателей: "] = cursor.fetchall()

        cursor.execute("SELECT * FROM stats_songs_with_min_listeners")
        query_tables["Песни c мин. слушателей: "] = cursor.fetchall()

        cursor.execute("SELECT * FROM stats_avg_unique_listeners")
        query_tables["Среднее кол-во уник. слушателей: "] = cursor.fetchall()

        cursor.execute("SELECT * FROM stats_most_listened_females")
        query_tables["Наиболее прослушиваемые женщинами: "] = cursor.fetchall()

        cursor.execute("SELECT * FROM stats_most_listened_males")
        query_tables["Наиболее прослушиваемые мужчинами: "] = cursor.fetchall()

        cursor.execute("SELECT * FROM stats_most_listened_youngsters")
        query_tables["Наиболее прослушиваемые молодежью: "] = cursor.fetchall()

        cursor.execute("SELECT * FROM stats_song_containing_in_most_playlists")
        query_tables["Песни, сод. в наиб кол-ве плейлистов: "] = cursor.fetchall()



        return query_tables

app = Flask(__name__)
app.config['SECRET_KEY'] = 'bc83989cdfdd894859fkdlfd83i489ffjdj99'
app.permanent_session_lifetime = datetime.timedelta(days=1)


@app.route("/", methods=['GET','POST']) 
def hub():
    session.permanent = True

    if session.get('user_data'):
        if (session['user_data']['email'] == 'admin@admin.ru'):

            db_connect('admin','admin')
            return redirect('/admin')
        
        db_connect('registered_user','user')
        
        print(connection.user)
        return redirect('/registered')

    #unregistered
    db_connect('guest','guest')

    songs = select_songs()
    if request.method == "POST" and request.form != [] and insert_survey_result(request.form):
        update_playlist(request.form)

    return render_template("unregistered_main.html", songs=songs)

@app.route("/registered", methods=['GET','POST'])
def registered():
    if connection.user == b'guest':
        abort(404)
        
    songs = select_songs()
    if request.method == "POST" and request.form != []:
        new_form = {'age':session['user_data']['age'],'sex':session['user_data']['sex'],'email':session['user_data']['email']}
        new_form.update(request.form.to_dict())
        if insert_survey_result(new_form):
            update_playlist(new_form)
        
    return render_template("registered_main.html", songs=songs, email=session['user_data']['email'])

@app.route("/admin", methods=['GET','POST']) 
def admin():
    if connection.user != b'admin':
        abort(404)

    songs = select_songs()
    if request.method == "POST" and request.form != []:
        new_form = {'age':session['user_data']['age'],'sex':session['user_data']['sex'],'email':session['user_data']['email']}
        new_form.update(request.form.to_dict())
        if insert_survey_result(new_form):
            update_playlist(new_form)

    return render_template("admin_main.html", songs=songs, email=session['user_data']['email'])

@app.route("/admin_statistics") 
def admin_statistics():
    if connection.user != b'admin':
        abort(404)
    for query_name in stat_query().keys():
           print(query_name)
        
    return render_template("admin_statistics.html", stat_queries=stat_query(), email=session['user_data']['email'])
    


@app.route("/registered_playlists")
def registered_playlists():
    if connection.user == b'guest':
        abort(404)

    
    playlists = get_ready_playlists()
    return render_template("registered_playlists.html", playlists=playlists.items(), email=session['user_data']['email'])

@app.route("/admin_playlists")
def admin_playlists():
    if connection.user != b'admin':
        abort(404)

    playlists = get_ready_playlists()
    return render_template("admin_playlists.html", playlists=playlists.items(),email=session['user_data']['email'])


@app.route("/login", methods=['GET','POST'])
def login():
    if request.method == "POST" and validate_user(request.form, session):
        return redirect('/')
    
    return render_template("login.html")


@app.route("/logout")
def logout():
    session['user_data'] = None
    return redirect('/')


@app.route("/register", methods=['GET','POST'])
def register():
    if request.method == 'POST' and insert_respondent(request.form):
        session['user_data'] = {'email':request.form['email'], 'sex':request.form['sex'], 'age': request.form['age']}
        return redirect('/')

    return render_template("register.html")


if __name__ == "__main__":
    app.run(debug=True)

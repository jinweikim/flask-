#coding:utf-8
from app import app
from flask import render_template,request,flash,session,redirect,url_for
import MySQLdb as mysql
db = mysql.connect(host='localhost',user='root',passwd='KING1218',db='mysystem')
c = db.cursor()
db.set_character_set('utf8')
c.execute('SET NAMES utf8;')
c.execute('SET CHARACTER SET utf8;')
c.execute('SET character_set_connection=utf8;')


@app.route('/',methods=['GET','POST'])
@app.route('/login',methods=['GET','POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        session['username'] = username
        sql = "SELECT identity FROM user WHERE user_name='%s'" % session['username']
        c.execute(sql)
        session['identity'] = c.fetchone()
        pwd = request.form['password']
        sql_user = "SELECT * FROM user WHERE user_name = '%s'" % username
        sql = "SELECT user_name FROM user WHERE user_name = '%s' AND password = '%s'" % (username, pwd)
        c.execute(sql_user)
        user_name = c.fetchone()
        flag = 0
        if c.rowcount == 0:
            error = '用户名不存在'
            flag = 1
        c.execute(sql)
        if c.rowcount == 0 and flag == 0:
            error = '密码错误'
        elif username == 'admin':
            session['username'] = request.form['username']
            return redirect(url_for('admin'))
        elif flag == 0:
            session['username'] = request.form['username']
            return render_template('hire.html',username=session['username'])
    return render_template('login.html', error=error)

@app.route('/hire',methods=['GET','POST'])
def hire():
    error = None
    if request.method == 'POST':
        if  request.form.get('sub','')=='租借':
            sql = "SELECT account FROM user WHERE user_name='%s'" % session['username']
            c.execute(sql)
            account = c.fetchone()
            sql = "SELECT identity FROM user WHERE user_name='%s'" % session['username']
            c.execute(sql)
            identity = c.fetchone()
            min = 0
            if identity[0]== 'stu_tea':
                min = 1
            else:
                min = 2
            sql = "SELECT whether_own FROM user WHERE user_name='%s'" % session['username']
            c.execute(sql)
            whether_own = c.fetchone()
            if whether_own[0] == 1:
                error = '你还有车未还哦'
                return render_template('hire.html',error=error)
            error = '租赁成功'
            if account[0] >= min:
                if 'company' in request.form:
                    choice = request.form.get('company','')
                c.execute( "SELECT company_id FROM com WHERE company_name = '%s' " % choice)
                company_id = c.fetchone()
                sql = "SELECT bike_id FROM bike WHERE company_id = '%d' AND status=1 " % company_id[0]
                c.execute(sql)
                bike_id = c.fetchone()
                if c.rowcount > 0:
                    sql = "INSERT INTO user_bike VALUES('%s','%d')" % (session['username'],bike_id[0])
                    c.execute(sql)
                    sql = "UPDATE bike SET status=0 WHERE bike_id= '%d'" % bike_id[0]
                    c.execute(sql)
                    sql = "UPDATE user SET account=account-'%d' WHERE user_name= '%s'" % (min,session['username'])
                    c.execute(sql)
                    sql = "UPDATE user SET whether_own=1 WHERE user_name= '%s'" % session['username']
                    c.execute(sql)
                    db.commit()
                else:
                    error = '无可用车辆'
            else:
                error = '账户余额不足'
        elif request.form['sub']=='还车':
            sql = "SELECT whether_own FROM user WHERE user_name='%s'" % session['username']
            c.execute(sql)
            own = c.fetchone()
            if own[0] == 1:
                sql = "SELECT bike_id FROM user_bike WHERE user_name='%s'" % session['username']
                c.execute(sql)
                bike_id=c.fetchone()
                sql = "UPDATE bike SET status=1  WHERE bike_id='%d'" % bike_id[0]
                c.execute(sql)
                sql = "UPDATE user SET whether_own=0  WHERE user_name='%s'" % session['username']
                c.execute(sql)
                sql = "SELECT bike.company_id " \
                      "FROM user_bike,bike " \
                      "WHERE user_bike.bike_id=bike.bike_id AND user_bike.user_name='%s'" % session['username']
                c.execute(sql)
                company_id = c.fetchone()
                #sql = "UPDATE com SET balance=balance+1 WHERE company_id='%d'" % company_id[0]
                #c.execute(sql)
                sql = "DELETE FROM user_bike WHERE user_name='%s'" % session['username']
                c.execute(sql)
                db.commit();
                error = '还车成功'
            else:
                error = '别着急，你还没有借车呢'
        return render_template('hire.html',error=error,username=session['username'])
    return render_template('hire.html',error=error,username=session['username'])

@app.route('/admin',methods=['GET','POST'])
def admin():
    sql = 'SELECT user.*,IFNULL(bike.bike_id,"无"),IFNULL(com.company_name,"无")' \
          'FROM ((user left join user_bike on user.user_name=user_bike.user_name) ' \
          'left join bike on user_bike.bike_id=bike.bike_id) ' \
          'left join com on bike.company_id=com.company_id'
    c.execute(sql)
    items = c.fetchall()
    if request.method == 'POST':
        error = None
        company = request.form['company']
        try:
            num = int(request.form['num'])
        except:
            error = "添加失败，添加数目不合法"
            return render_template('admin.html',items=items,error=error)
        if num < 0:
            error = "添加失败，添加数目不可以小于0"
            return render_template('admin.html', items=items,error=error)
        sql = "SELECT company_id FROM com WHERE company_name = '%s' " % company
        c.execute(sql)
        company_id = c.fetchone()
        for i in range(num):
            sql = "INSERT INTO bike (company_id,status) VALUES('%d','1')" % company_id[0]
            c.execute(sql)
        sql = "UPDATE com SET balance=balance+'%d' WHERE company_id='%d'" %(num,company_id[0])
        c.execute(sql)
        db.commit()
        error = '添加成功'
        return render_template('admin.html',items=items,error=error)
    return render_template('admin.html',items=items)

@app.route('/user',methods=['GET','POST'])
def user():
    sql = "SELECT * FROM user_bike WHERE user_name='%s'" % session['username']
    c.execute(sql)
    records = c.fetchall()
    error = None
    if request.method == 'POST':
        oldpassword = request.form['oldpassword']
        sql = "SELECT password FROM user WHERE user_name='%s'" % session['username']
        c.execute(sql)
        password = c.fetchone()
        if password[0] == oldpassword:
            newpassword = request.form['newpassword']
            if not newpassword.strip():
                error = '新密码不可为空'
                return render_template('user.html', records=records, username=session['username'], error=error)
            try:
                sql = "UPDATE user SET password='%s' WHERE user_name='%s'" % (newpassword,session['username'])
                c.execute(sql)
            except Exception,e:
                error = e.args[1]
                return render_template('user.html', records=records, username=session['username'], error=error)
            db.commit()
            error = '修改成功'
        else:
            error = '原密码错误'
        return render_template('user.html', records=records, username=session['username'], error=error)

    return render_template('user.html',records=records,username=session['username'],error=error)


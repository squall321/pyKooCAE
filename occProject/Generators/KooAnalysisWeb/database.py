import os
import os.path
import sys

from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, ForeignKey, DateTime, Boolean, Float
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy import select, delete

basedir = os.path.abspath(os.path.dirname(__file__))
dbPath = 'sqlite:///' + os.path.join(basedir, 'datasqlite.db')

engine = create_engine(dbPath)
metadata = MetaData()
db_session = scoped_session(sessionmaker(autocommit=False, 
                                         autoflush=False, 
                                         bind=engine))

BaseDB = declarative_base()
BaseDB.query = db_session.query_property()

def init_db():
    metadata.create_all(bind=engine)

def init_user_table():
    from KooAnalysisWeb import User
    address_table = Table("users",
                          metadata,
                          Column('employee_number', Integer, primary_key=True),
                          Column("id", String, primary_key=True),
                          Column('name',String)
    )
    metadata.create_all(bind=engine)
def add_user(name,id,employee_number):
    from KooAnalysisWeb import User
    conn = engine.connect()
    sel_exist = select(User).where(User.employee_number == employee_number)
    result = conn.execute(sel_exist)
    rfa = result.fetchall()
    print(rfa)
    if len(rfa) == 0:
        u = User(name=name,id=id,employee_number=employee_number)
        db_session.add(u)
        db_session.commit()
        print("유저가 생성 되었습니다. ")
        db_session.close()
        return True
    else:
        curuser = rfa[0] 
        curid = curuser['id']
        curname = curuser['name']
        if id == curid:
            if name == curname:
                print("로그인 되었습니다.")
                db_session.close()
                return True
            print("이름이 다릅니다.")
            return False
        
def remove_user(employee_number):
    from KooAnalysisWeb import User
    conn = engine.connect()
    sel_exist = select(User).where(User.employee_number == employee_number)
    result = conn.execute(sel_exist)
    rfa = result.fetchall()
    print(rfa)
    if len(rfa) == 0:
        print("유저가 없습니다.")
        return False
    else:
        curuser = rfa[0] 
        curid = curuser['id']
        curname = curuser['name']
        db_session.delete(curuser)
        db_session.commit()
        print("유저가 삭제 되었습니다. ")
        db_session.close()
        return True    
            
def show_users():
    from KooAnalysisWeb import User
    conn = engine.connect()
    sel_all = select(User)
    result = conn.execute(sel_all)
    for i in result:
        print(i)
    db_session.close()

if __name__ == '__main__':
    if len(sys.argv)<2:
        print('입력 keyword가 존재하지 않습니다.')
        print('DB 초기화 : python INIT')
        print('유저 추가 : python ADDUSER [name] [id] [employee_number]')
    elif sys.argv[1] == 'INIT':
        init_db()
    elif sys.argv[1] == 'INITUSERTABLE':
        init_user_table()
    elif sys.argv[1] == 'SHOWUSERS':
        show_users()
    elif sys.argv[1] == 'ADDUSER':
        if len(sys.argv)>=5:
            add_user(sys.argv[2],sys.argv[3],sys.argv[4])
        else:
            print('입력 변수의 수가 부족합니다. {length}/5'.format(length=len(sys.argv)))
    elif sys.argv[1] == 'REMOVEUSER':
        if len(sys.argv)>=3:
            remove_user(sys.argv[2])
        else:
            print('입력 변수의 수가 부족합니다. {length}/3'.format(length=len(sys.argv)))



    
    

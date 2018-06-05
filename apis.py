import uuid

import os
from flask import request
from flask_restful import Api, Resource, marshal_with, fields, marshal, reqparse
from sqlalchemy import or_
from werkzeug.datastructures import FileStorage

import settings
from models import *
from dao import queryAll, queryById, add, delete, query

api = Api()


def init_api(app):
    api.init_app(app)


class UserApi(Resource):
    def get(self):
        key = request.args.get('key')
        if key:
            result = {'state': 'fail',
                      'msg': '无'}
            qs = query(User).filter(or_(User.id == key,
                                        User.name == key,
                                        User.phone == key))
            if qs.count():
                result['state'] = 'ok'
                result['msg'] = '成功'
                result['data'] = qs.first().json
            return result

        users = queryAll(User)

        return {'state': 'ok',
                'data': [user.json for user in users]}

    def post(self):
        # 从上传的form对象中取出name和phone
        name = request.form.get('name')
        phone = request.form.get('phone')

        print(name, phone)
        # 数据存入到数据库
        user = User()
        user.name = name
        user.phone = phone

        add(user)  # 添加到数据库

        return {"state": "ok",
                "msg": '添加 {} 用户成功!'.format(name)}

    def delete(self):
        id = request.args.get('id')
        user = queryById(User, id)
        delete(user)
        return {'state': 'ok',
                'msg': '删除{}成功'.format()}

    def put(self):
        id = request.form.get('id')
        user = queryById(User, id)
        user.name = request.form.get('name')
        user.phone = request.form.get('phone')

        add(user)
        return {'state': 'ok',
                'msg': user.name + '更新成功!'}


class ImageApi(Resource):
    # 设置图片Image对象输出的字段
    img_fields = {"id": fields.Integer,
                  "name": fields.String,
                  # "img_url": fields.String(attribute='url'),
                  "url": fields.String,
                  "size": fields.Integer(default=0)}
    get_out_fields = {
        "state": fields.String(default='ok'),
        "data": fields.Nested(img_fields),
        "size": fields.Integer(default=1)
    }

    # 输入的定制
    parser = reqparse.RequestParser()
    parser.add_argument('id',
                        type=int,  # 参数类型
                        required=False,  # 是否必须要
                        help='请提供id参数')  # 必须的参数不存在是的错误提示

    # @marshal_with(get_out_fields)
    def get(self):
        self.parser.parse_args()  # 解析参数，如果参数不满足，则直接返回

        id = request.args.get('id')
        if id:
            img = query(Image).filter(Image.id == id).first()

            # 将对象转成输出的字段格式（json格式）
            return marshal(img, self.img_fields)
        else:
            # 查询所有Image
            images = queryAll(Image)
            data = {"data": images,
                    "size": len(images)}
            return marshal(data, self.get_out_fields)


class MusicApi(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('key', dest='name', type=str, required=True, help='必须提供name搜索的关键字')
    parser.add_argument('id', type=int, help='请确定id的参数类型')
    parser.add_argument('tag', action='append', required=True, help='至少提供一个tag标签')
    parser.add_argument('session', location='cookies', required=True, help='cookie中不存在session')

    music_fields = {
        'id': fields.Integer,
        'name': fields.String,
        'singer': fields.String,
        'url': fields.String(attribute='mp3_url')
    }
    out_fields = {
        'state': fields.String(default='ok'),
        'msg': fields.String(default='查询成功'),
        'data': fields.Nested(music_fields)
    }

    def get(self):
        args = self.parser.parse_args()
        name = args.get('name')
        tags = args.get('tag')

        session = args.get('session')

        musics = query(Music).filter(Music.name.like('%{}%'.format(name)))
        if musics.count():
            return {'data': musics.all()}
        return {'msg': '没有'}


class UploadApi(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument("img", type=FileStorage,
                        location='files',
                        require=True,
                        help='必须提供一个名为img的File表单')

    def post(self):
        args = self.parser.parse_args()

        uFile: FileStorage = args.get('img')

        newFileName = str(uuid.uuid4().replace('-', ''))
        newFileName += "." + uFile.filename.split('.')[-1]
        uFile.save(os.path.join(settings.MEDIA_DIR, newFileName))

        return {'msg': '上传成功', 'path': '/static/uploads/aaa.jpg'}


# 将资源添加到api对象中，并声明uri
# -------------------------------
api.add_resource(UserApi, '/user/')
api.add_resource(ImageApi, '/images/')
api.add_resource(MusicApi, '/music/')
api.add_resource(UploadApi, '//')

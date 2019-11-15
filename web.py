import pymongo
from bottle import route, run,  request, static_file
import re
import pymongo

id_names = {'1402400261': '爱可可-爱生活', }
print(list(id_names.keys()))

@route('/imgs/<filename>')
def server_image(filename):
    return static_file(filename, root='./imgs/')


@route('/videos/<filename>')
def server_video(filename):
    return static_file(filename, root='./videos/')


@route('/', method='GET')
def index():
    myclient = pymongo.MongoClient("mongodb://127.0.0.1:27017/")
    mydb = myclient["db_weibo"]
    db_mblogs = mydb['db_mblogs']
    db_videos = mydb['db_videos']
    htext = '<html><head><style>\
    @media (min-width: 1100px) {\
  .center{ max-width:60%;}\
}\
       </style></head><body> <div style="margin:auto;background:white;" class="center">'
    for i in db_mblogs.find({"uid": {"$in": list(id_names.keys())}}).sort('_id', direction=-1).limit(150):
        htext += '<div style="margin-top:40px;padding:20px;border: 1px solid black;background:#f2f2f2;letter-spacing:2px;font-size:32px">' + \
            '<div style="color:red">' + id_names[i['uid']]+':</div>' +\
            '<p style="text-indent:30px">'+i['text']+'</p>'
        if len(i['imgs']) > 0:
            images = i['imgs'].split('\t')
            for img in images:
                image_width = (1/len(images))*100
                htext += f"<image src='imgs/{img.split('/')[-1]}' style='max-height:400px;max-width:400px;width:{image_width}%'></image>"
        if 'object_id' in i.keys() and len(i['object_id']) > 0:
            video_name = db_videos.find({'object_id': i['object_id']})
            src = ''
            for v in video_name:
                src = v['video_name']
                # <video><source src="" type="video/mp4"></video>
                htext += f"<video autoplay='true' controls height='300px'><source src='videos/{src}' type='video/mp4'></video>"
        htext += '</div>'
    htext += '</div></body></html>'
    return htext


if __name__ == "__main__":
    run(host='0.0.0.0', port=8088, server='paste')

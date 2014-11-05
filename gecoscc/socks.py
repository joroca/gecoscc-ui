import datetime

import redis
import simplejson as json

from socketio.namespace import BaseNamespace
from socketio import socketio_manage

td365 = datetime.timedelta(days=365)
td365seconds = int((td365.microseconds +
                    (td365.seconds + td365.days * 24 * 3600) * 10 ** 6) / 10 ** 6)

CHANNEL_WEBSOCKET = 'message'
SESSION_SOCKET_ID = 'socked_session_id'


def get_manager(request):
    return redis.Redis()


def invalidate_change(request, schema_detail, objtype, objnew, objold):
    manager = get_manager(request)
    manager.publish(CHANNEL_WEBSOCKET, json.dumps({
        'session_socket_id_emitter': request.session.get(SESSION_SOCKET_ID, ''),
        'action': 'change',
        'object': schema_detail().serialize(objnew)
    }))


def invalidate_delete(request, schema_detail, objtype, obj):
    manager = get_manager(request)
    manager.publish(CHANNEL_WEBSOCKET, json.dumps({
        'session_socket_id_emitter': request.session.get(SESSION_SOCKET_ID, ''),
        'action': 'delete',
        'object': schema_detail().serialize(obj)
    }))


def invalidate_jobs(request):
    manager = get_manager(request)
    manager.publish(CHANNEL_WEBSOCKET, json.dumps({
        'session_socket_id_emitter': request.session.get(SESSION_SOCKET_ID, ''),
        'action': 'jobs',
        'object': None
    }))


class GecosNamespace(BaseNamespace):

    # Create the websocket

    def listener(self):
        r = redis.StrictRedis()
        r = r.pubsub()

        r.subscribe(CHANNEL_WEBSOCKET)

        for m in r.listen():
            if m['type'] == 'message':
                data = json.loads(m['data'])
                self.emit(CHANNEL_WEBSOCKET, data)

    def on_subscribe(self, *args, **kwargs):
        remaining = self.request.matchdict.get('remaining', None)
        if remaining:
            try:
                self.request.session[SESSION_SOCKET_ID] = remaining[2]
                self.request.session._session().save()
            except IndexError:
                pass
        self.spawn(self.listener)

    def on_close(self, *args, **kwargs):
        pass

    # End Create the websocket

    # Publish the message
    def on_message(self, msg):
        r = redis.Redis()
        r.publish(CHANNEL_WEBSOCKET, msg)


def socketio_service(request):
    retval = socketio_manage(request.environ,
                             {'': GecosNamespace},
                             request=request)

    return retval

